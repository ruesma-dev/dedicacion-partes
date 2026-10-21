# tests/test_f030_r30_editar.py
"""F-030 · Anexo R30 en el transfer: cambiar los días de una incidencia ya
registrada EDITA la `fec` de sus líneas (R40-R46,
ARCHITECTURE.md#regla-incidencia).

- Contrato (T27): la incidencia trae la traza de la api (`hmores_ide_*`,
  `dia_*`, opcionales) y la acción `editar` publica `fec_antes`.
- Cliente (T28): la lectura de R33 trae `can`, parte y estado y busca
  también por `ide`; el `UPDATE` de la `fec` lleva la guarda de F-051.
- Reglas (T29): `reconciliar`, pura.
- Preflight, lote (T30) y `ejecutar` (T31).

Sin red ni BBDD: el cliente con su `_read` sustituido por un doble y el
pipeline con los dobles de `conftest.py`. Los `ide` son inventados.
"""
from __future__ import annotations

import pytest
from domain.models.registro_models import (
    AccionIncidencia,
    IncidenciaEntrada,
    LineaIncidenciaSigrid,
)

from tests.conftest import OBRA_ORIGEN, linea
from tests.test_f030_pipeline_incidencias import (
    CLAVES_INC,
    ClienteInc,
    _json_inc,
    _json_linea,
)

TRAZA = {"hmores_ide_ini": 9001, "hmores_ide_fin": 9002, "dia_ini": 5,
         "dia_fin": 9}


@pytest.fixture
def api(monkeypatch):
    """La app real con el cliente que se le dé (como la de
    `test_f030_pipeline_incidencias`)."""
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from interface_adapters.api import app as modulo_app

    from tests.test_f050_endpoint_propuesta import AJUSTES

    def fabricar(cli, **ajustes):
        monkeypatch.setattr(modulo_app, "SigridWriteClient", lambda **kw: cli)
        st = SimpleNamespace(**{**AJUSTES, "sigrid_lecturas_paralelas": 4,
                                **ajustes})
        return TestClient(modulo_app.build_app(st))
    return fabricar


# ============================ contrato (T27) ============================ #
def test_f030_r30_contrato_entrada_con_la_traza_opcional():
    from interface_adapters.api.app import IncidenciaIn

    sin = IncidenciaEntrada(id=7, recurso_ide=200, empresa=1, codigo="CIV",
                            ano=2026, mes=7, desde=5, hasta=9)
    assert (sin.hmores_ide_ini, sin.hmores_ide_fin, sin.dia_ini,
            sin.dia_fin) == (None,) * 4
    entrada = IncidenciaEntrada(**IncidenciaIn(**_json_inc(**TRAZA)).model_dump())
    assert (entrada.hmores_ide_ini, entrada.hmores_ide_fin, entrada.dia_ini,
            entrada.dia_fin) == (9001, 9002, 5, 9)
    assert IncidenciaIn(**_json_inc()).hmores_ide_ini is None


def test_f030_r30_contrato_accion_y_linea_con_los_campos_nuevos():
    a = AccionIncidencia(id=7, rol="ini", accion="editar", fecha_int=20260706)
    assert (a.fec_antes, a.hmoide) == (None, None)
    ls = LineaIncidenciaSigrid(51, 200, 20260705, "CIV", "porcentajes:inc:7:ini",
                               "PT26/1")
    assert (ls.can, ls.hmoide, ls.parte_est) == (None, None, None)


def test_f030_r46_contrato_solo_editar_publica_fec_antes():
    from interface_adapters.api.app import _con_incidencias

    editar = AccionIncidencia(id=7, rol="ini", accion="editar",
                              fecha_int=20260706, fec_antes=20260705,
                              hmores_ide=9001, hmoide=777)
    ya = AccionIncidencia(id=7, rol="fin", accion="ya_registrado",
                          fecha_int=20260709, hmores_ide=9002)
    r = _con_incidencias({}, [editar, ya])
    assert set(r["incidencias"][0]) == CLAVES_INC | {"fec_antes"}
    assert r["incidencias"][0]["fec_antes"] == 20260705
    assert set(r["incidencias"][1]) == CLAVES_INC
    assert "hmoide" not in r["incidencias"][0]          # interno


def test_f030_r30_contrato_sin_los_campos_responde_igual(api):
    peticion = {"obra": {"codigo": OBRA_ORIGEN}, "lineas": [_json_linea(1)],
                "incidencias": [_json_inc()]}
    hoy = api(ClienteInc()).post("/api/registro/preflight",
                                 json=peticion).json()
    nulos = api(ClienteInc()).post("/api/registro/preflight", json={
        **peticion, "incidencias": [_json_inc(
            hmores_ide_ini=None, hmores_ide_fin=None, dia_ini=None,
            dia_fin=None)]}).json()
    assert nulos == hoy and hoy["ok"] is True
    assert [set(x) for x in hoy["incidencias"]] == [CLAVES_INC] * 2


# ============================ cliente (T28) ============================= #
from tests.test_f050_propuesta import _cliente_historial

FILA = {"ide": 9001, "reside": 200, "fec": 20260705, "cod": "CIV ",
        "synckey": " porcentajes:inc:7:ini ", "parte": " PT26/1 ", "can": 0,
        "hmoide": 777, "est": 1}
SELECT = ("SELECT h.ide AS ide, h.reside AS reside, h.fec AS fec, "
          "a.cod AS cod, h.synckey AS synckey, c.cod AS parte, "
          "h.can AS can, h.hmoide AS hmoide, c.est AS est FROM hmores h "
          "JOIN auxhor a ON a.ide = h.horide JOIN hmo m ON m.ide = h.hmoide "
          "JOIN con c ON c.ide = m.ide ")
GUARDA_INC = (
    "WHERE ide = ? AND reside = ? AND ABS(ISNULL(can, 0) - ?) < 0.000001 "
    "AND LTRIM(RTRIM(ISNULL(synckey, ''))) = ? "
    "AND ISNULL(dvaproide, 0) = 0 AND ISNULL(dvfproide, 0) = 0 "
    "AND ISNULL(hdereside, 0) = 0 AND ISNULL(empdpreide, 0) = 0 "
    "AND ISNULL(empabside, 0) = 0 AND ISNULL(emprccide, 0) = 0 "
    "AND EXISTS (SELECT 1 FROM auxhor a WHERE a.ide = hmores.horide "
    "AND a.cod = ?) "
    "AND EXISTS (SELECT 1 FROM con c WHERE c.ide = hmores.hmoide "
    "AND c.est = ?)")


def test_f030_r40_sql_por_recurso_o_por_ide_con_can_parte_y_estado():
    cli, falso = _cliente_historial([
        FILA, dict(FILA, ide=9002, can=None, hmoide=None, est=None,
                   cod="CIP")])
    filas = cli.incidencias_del_mes([300, 200], 2026, 7, ides=[9002, None,
                                                                 9001, 9001])
    [(sql, params)] = falso.llamadas
    assert sql == SELECT + (
        "WHERE (h.reside IN (?,?) AND h.fec BETWEEN ? AND ? "
        "AND a.cod LIKE ? OR h.ide IN (?,?)) ORDER BY h.ide")
    assert params == [200, 300, 20260701, 20260731, "CI%", 9001, 9002]
    assert filas == [
        LineaIncidenciaSigrid(9001, 200, 20260705, "CIV",
                              "porcentajes:inc:7:ini", "PT26/1", can=0.0,
                              hmoide=777, parte_est=1),
        LineaIncidenciaSigrid(9002, 200, 20260705, "CIP",
                              "porcentajes:inc:7:ini", "PT26/1", can=None,
                              hmoide=None, parte_est=None)]
    assert isinstance(filas[0].can, float)


def test_f030_r40_sql_sin_ides_el_where_de_hoy():
    cli, falso = _cliente_historial()
    cli.incidencias_del_mes([200], 2026, 7)
    [(sql, params)] = falso.llamadas
    assert sql == SELECT + (
        "WHERE h.reside IN (?) AND h.fec BETWEEN ? AND ? "
        "AND a.cod LIKE ? ORDER BY h.ide")
    assert params == [200, 20260701, 20260731, "CI%"]


def test_f030_r40_sql_en_pruebas_el_filtro_de_partes_a_todo():
    cli, falso = _cliente_historial()
    cli.incidencias_del_mes([200], 2026, 7, hmoides=[12, 11], ides=[9001])
    [(sql, params)] = falso.llamadas
    assert sql.endswith("a.cod LIKE ? OR h.ide IN (?)) "
                        "AND h.hmoide IN (?,?) ORDER BY h.ide")
    assert params == [200, 20260701, 20260731, "CI%", 9001, 11, 12]
    cli, falso = _cliente_historial()
    assert cli.incidencias_del_mes([200], 2026, 7, hmoides=[],
                                   ides=[9001]) == []
    assert falso.llamadas == []


def test_f030_r40_sql_solo_ides_y_trozos_sin_repetir():
    cli, falso = _cliente_historial()
    cli.incidencias_del_mes([None], 2026, 7, ides=[9001])
    [(sql, params)] = falso.llamadas
    assert sql == SELECT + "WHERE (h.ide IN (?)) ORDER BY h.ide"
    assert params == [9001]
    # 600 recursos y 2 `ide`: 500 recursos y luego 100 más los 2 `ide`; la
    # línea que sale en los dos trozos, una vez.
    cli, falso = _cliente_historial([FILA])
    filas = cli.incidencias_del_mes(range(1, 601), 2026, 7, ides=[9001, 9002])
    assert [len(p) for _, p in falso.llamadas] == [503, 105]
    assert falso.llamadas[1][1][-2:] == [9001, 9002]
    assert "OR h.ide IN" not in falso.llamadas[0][0]
    assert [f.ide for f in filas] == [9001]


def test_f030_r41_sql_editar_la_fec_con_la_guarda_de_su_codigo():
    cli, _ = _cliente_historial()
    st = cli.stmt_editar_fecha_incidencia(
        ide=9001, reside=200, hora_codigo="CIV", synckey_leida=" k ",
        fecha_int=20260706)
    assert " ".join(st["sql"].split()) == "UPDATE hmores SET fec = ? " + GUARDA_INC
    assert st["parameters"] == [20260706, 9001, 200, 0.0, "k", "CIV", 1]
    sin_sk = cli.stmt_editar_fecha_incidencia(
        ide="9002", reside="200", hora_codigo=" CIZ ", synckey_leida=None,
        fecha_int="20260712")
    assert sin_sk["parameters"] == [20260712, 9002, 200, 0.0, "", "CIZ", 1]


def test_f030_r41_sql_la_guarda_sin_codigo_es_la_de_f051():
    cli, _ = _cliente_historial()
    assert cli._guarda(1, 2, 0.5, "k") == cli._guarda(1, 2, 0.5, "k", None)
    texto, params = cli._guarda(1, 2, 0.5, "k", "CIV")
    assert "a.cod = ?" in texto and "LIKE 'M%'" not in texto
    assert params == [1, 2, 0.5, "k", "CIV", 1]


# ======================== reconciliar (T29) ============================= #
from domain.models.registro_models import HoraRecurso

HORAS = {200: [HoraRecurso(71, "CIV", "Vacaciones(V)", 12.5),
               HoraRecurso(72, "CIE", "Enfermedad(B)", 0.0),
               HoraRecurso(79, "CIZ", "Fin de Incidencia", 0.0)]}
EST = 1


def _entrada(id_=7, desde=6, hasta=9, traza=True, **kw) -> IncidenciaEntrada:
    base = {"id": id_, "recurso_ide": 200, "empresa": 1, "codigo": "CIV",
            "ano": 2026, "mes": 7, "desde": desde, "hasta": hasta,
            **(TRAZA if traza else {})}
    return IncidenciaEntrada(**{**base, **kw})


def _par(entrada):
    from application.services.reglas_incidencias import decidir_incidencia

    return decidir_incidencia(entrada, HORAS)


def _linea(ide, fec, cod="CIV", sk=None, *, reside=200, can=0.0, parte="PT26/1",
           hmoide=777, est=EST):
    return LineaIncidenciaSigrid(ide, reside, fec, cod, sk, parte, can=can,
                                 hmoide=hmoide, parte_est=est)


def _el_par(ini=20260705, fin=20260709, **kw):
    return [_linea(9001, ini, "CIV", "porcentajes:inc:7:ini", **kw),
            _linea(9002, fin, "CIZ", "porcentajes:inc:7:fin", **kw)]


def _rec(entradas, existentes, est=EST):
    from application.services.reglas_incidencias import reconciliar

    acciones = [a for e in entradas for a in _par(e)]
    reconciliar(acciones, entradas, existentes, est=est)
    return acciones


def _v(acciones):
    return [(a.rol, a.accion, a.fecha_int, a.fec_antes, a.hmores_ide,
             a.hmoide, a.parte_cod) for a in acciones]


def test_f030_r40_misma_fec_ya_registrado_por_ide_o_por_synckey():
    from application.services.reglas_incidencias import MOTIVO_INC_YA

    acc = _rec([_entrada(desde=5)], _el_par())
    assert _v(acc) == [("ini", "ya_registrado", 20260705, None, 9001, 777,
                        "PT26/1"),
                       ("fin", "ya_registrado", 20260709, None, 9002, 777,
                        "PT26/1")]
    assert acc[0].motivo == MOTIVO_INC_YA.format(ide=9001)
    # Sin la traza de la api (registrada antes del anexo): por su synckey.
    acc = _rec([_entrada(desde=5, traza=False)], _el_par())
    assert [(a.accion, a.hmores_ide) for a in acc] == [
        ("ya_registrado", 9001), ("ya_registrado", 9002)]


def test_f030_r40_nuestra_solo_si_es_del_recurso_y_con_nuestra_synckey():
    otro_recurso = [_linea(9001, 20260705, "CIV", "porcentajes:inc:7:ini",
                           reside=999)]
    acc = _rec([_entrada(desde=5, hasta=9)], otro_recurso)
    assert acc[0].accion == "escribir"           # no es la nuestra
    otra_sk = [_linea(9001, 20260705, "CIV", "partes:9:1")]
    acc = _rec([_entrada(desde=6, hasta=9)], otra_sk)
    assert acc[0].accion == "escribir"           # ya no está: se escribe


def test_f030_r41_otra_fec_edita_y_cada_linea_se_decide_sola():
    acc = _rec([_entrada(desde=6, hasta=9)], _el_par())
    assert _v(acc) == [
        ("ini", "editar", 20260706, 20260705, 9001, 777, "PT26/1"),
        ("fin", "ya_registrado", 20260709, None, 9002, 777, "PT26/1")]
    assert acc[0].motivo is None
    acc = _rec([_entrada(desde=12, hasta=14)], _el_par())
    assert [(a.accion, a.fec_antes) for a in acc] == [
        ("editar", 20260705), ("editar", 20260709)]


def test_f030_r41_sin_dia_en_la_traza_edita_si_es_del_mes():
    sin_dias = {"dia_ini": None, "dia_fin": None}
    acc = _rec([_entrada(desde=6, **sin_dias)], _el_par())
    assert acc[0].accion == "editar"
    # Por `synckey` en otro mes (no consta el día): no se cambia de mes.
    acc = _rec([_entrada(desde=6, traza=False)],
               _el_par(ini=20260630, fin=20260709))
    assert acc[0].accion == "omitir"


@pytest.mark.parametrize("cambio", [
    {"ini": 20260704},                       # su fec, cambiada a mano
    {"ini": 20260605},                       # a otro mes
])
def test_f030_r42_cambiada_en_sigrid_no_se_toca(cambio):
    from application.services.reglas_incidencias import MOTIVO_INC_CAMBIADA

    acc = _rec([_entrada(desde=6)], _el_par(**cambio))
    assert (acc[0].accion, acc[0].hmores_ide, acc[0].fec_antes) == (
        "omitir", 9001, None)
    assert acc[0].motivo == MOTIVO_INC_CAMBIADA.format(ide=9001)
    assert "cambiada en Sigrid" in acc[0].motivo


@pytest.mark.parametrize("linea", [
    _linea(9001, 20260705, "CIE", "porcentajes:inc:7:ini"),    # otro código
    _linea(9001, 20260705, None, "porcentajes:inc:7:ini"),
    _linea(9001, 20260705, "CIV", "porcentajes:inc:7:ini", can=1.0),
])
def test_f030_r42_otro_codigo_o_can_no_se_toca(linea):
    acc = _rec([_entrada(desde=6)], [linea])
    assert acc[0].accion == "omitir"
    # Con su fec pedida, ya registrada aunque le cambien el `can` (D14).
    acc = _rec([_entrada(desde=5)], [linea])
    assert acc[0].accion == "ya_registrado"


def test_f030_r42_can_nulo_cuenta_como_cero():
    acc = _rec([_entrada(desde=6)], _el_par(can=None))
    assert acc[0].accion == "editar"


def test_f030_r43_parte_cerrado_no_se_edita():
    from application.services.reglas_incidencias import MOTIVO_INC_CERRADO

    acc = _rec([_entrada(desde=6, hasta=12)], _el_par(est=3))
    assert [a.accion for a in acc] == ["omitir", "omitir"]
    assert acc[0].motivo == MOTIVO_INC_CERRADO.format(parte="PT26/1",
                                                      desde=5, hasta=9)
    assert acc[0].motivo == "el parte PT26/1 está cerrado: sigue del 5 al 9"
    # Con su fec, ya registrada aunque el parte esté cerrado.
    acc = _rec([_entrada(desde=5, hasta=12)], _el_par(est=3))
    assert [a.accion for a in acc] == ["ya_registrado", "omitir"]


def test_f030_r44_dia_ocupado_por_otra_igual_no_se_edita():
    from application.services.reglas_incidencias import MOTIVO_INC_DUPLICADA

    otra = _linea(60, 20260706, "CIV", "partes:9:1", parte="PT26/9")
    acc = _rec([_entrada(desde=6)], [*_el_par(), otra])
    assert (acc[0].accion, acc[0].parte_cod) == ("omitir", "PT26/1")
    assert acc[0].motivo == MOTIVO_INC_DUPLICADA.format(
        cod="CIV", dia=6, mes=7, parte="PT26/9")
    # Otro código, otro recurso u otro día: no ocupa.
    libres = [_linea(61, 20260706, "CIE"), _linea(62, 20260706, reside=201),
              _linea(63, 20260707)]
    acc = _rec([_entrada(desde=6)], [*_el_par(), *libres])
    assert acc[0].accion == "editar"


def test_f030_r44_con_las_ediciones_de_la_peticion_aplicadas():
    """La 8 se va del 6 al 20: la 7 puede ocupar el 6. La 9 iría al 25,
    donde la 10 se queda (su parte está cerrado): no se edita."""
    par8 = [_linea(9011, 20260706, "CIV", "porcentajes:inc:8:ini"),
            _linea(9012, 20260722, "CIZ", "porcentajes:inc:8:fin")]
    acc = _rec([_entrada(desde=6), _entrada(8, desde=20, hasta=22,
                                            traza=False)],
               [*_el_par(), *par8])
    assert [(a.id, a.rol, a.accion) for a in acc] == [
        (7, "ini", "editar"), (7, "fin", "ya_registrado"),
        (8, "ini", "editar"), (8, "fin", "ya_registrado")]
    par9 = [_linea(9021, 20260723, "CIV", "porcentajes:inc:9:ini"),
            _linea(9022, 20260724, "CIZ", "porcentajes:inc:9:fin")]
    par10 = [_linea(9031, 20260725, "CIV", "porcentajes:inc:10:ini", est=3),
             _linea(9032, 20260726, "CIZ", "porcentajes:inc:10:fin", est=3)]
    acc = _rec([_entrada(9, desde=25, hasta=26, traza=False),
                _entrada(10, desde=27, hasta=28, traza=False)],
               [*par9, *par10])
    assert [(a.id, a.rol, a.accion) for a in acc] == [
        (9, "ini", "omitir"), (9, "fin", "omitir"),
        (10, "ini", "omitir"), (10, "fin", "omitir")]
    # En cadena: la 11 no puede ir al 15 (otra igual) y se queda en el 12,
    # así que la 12, que iba a ocupar ese 12 (y se decide antes), tampoco.
    # Su fin sí: el 13 lo deja libre el fin de la 11.
    par11 = [_linea(9041, 20260712, "CIV", "porcentajes:inc:11:ini"),
             _linea(9042, 20260713, "CIZ", "porcentajes:inc:11:fin")]
    par12 = [_linea(9051, 20260710, "CIV", "porcentajes:inc:12:ini"),
             _linea(9052, 20260711, "CIZ", "porcentajes:inc:12:fin")]
    otra = _linea(70, 20260715, "CIV", "partes:1:1")
    acc = _rec([_entrada(12, desde=12, hasta=13, traza=False),
                _entrada(11, desde=15, hasta=16, traza=False)],
               [*par11, *par12, otra])
    assert [(a.id, a.rol, a.accion) for a in acc] == [
        (12, "ini", "omitir"), (12, "fin", "editar"),
        (11, "ini", "omitir"), (11, "fin", "editar")]


def test_f030_r27_sin_la_nuestra_como_siempre_y_con_lo_movido():
    from application.services.reglas_incidencias import MOTIVO_INC_DUPLICADA

    otra = _linea(60, 20260712, "CIV", None, parte="PT26/40")
    acc = _rec([_entrada(desde=12, hasta=14, traza=False)], [otra])
    assert (acc[0].accion, acc[0].parte_cod, acc[0].motivo) == (
        "omitir", "PT26/40", MOTIVO_INC_DUPLICADA.format(
            cod="CIV", dia=12, mes=7, parte="PT26/40"))
    assert (acc[1].accion, acc[1].parte_cod) == ("escribir", None)
    # Una nueva el 5, donde estaba la 7, que se mueve al 6: se escribe.
    acc = _rec([_entrada(desde=6), _entrada(8, desde=5, hasta=5,
                                            traza=False, codigo="CIV")],
               _el_par())
    assert [(a.id, a.rol, a.accion) for a in acc][:3] == [
        (7, "ini", "editar"), (7, "fin", "ya_registrado"),
        (8, "ini", "escribir")]


def test_f030_r40_solo_se_reconcilian_las_que_se_escribirian():
    from application.services.reglas_incidencias import reconciliar

    omitidas = _par(_entrada(desde=6, recurso_ide=300))      # sin códigos
    antes = [(a.accion, a.motivo) for a in omitidas]
    reconciliar(omitidas, [_entrada(desde=6, recurso_ide=300)], _el_par(),
                est=EST)
    assert [(a.accion, a.motivo) for a in omitidas] == antes
    assert reconciliar([], [], _el_par(), est=EST) is None


def test_f030_r43_sin_la_otra_linea_su_dia_no_consta():
    from application.services.reglas_incidencias import MOTIVO_INC_CERRADO

    acc = _rec([_entrada(desde=6, hasta=12)], _el_par(est=3)[:1])
    assert acc[0].motivo == MOTIVO_INC_CERRADO.format(parte="PT26/1",
                                                      desde=5, hasta="?")


# ====================== preflight y lote (T30) ========================== #
from tests.test_f030_pipeline_incidencias import (
    OBRA,
    OBRA_B,
    _ajustes,
    _lote,
    _pf,
    _suelto,
)
from tests.test_f030_pipeline_incidencias import _inc as _inc_pf


def _par_sigrid(ini=20260705, fin=20260709, est=1):
    return [LineaIncidenciaSigrid(9001, 200, ini, "CIV", "porcentajes:inc:7:ini",
                                  "PT26/00251", can=0.0, hmoide=777,
                                  parte_est=est),
            LineaIncidenciaSigrid(9002, 200, fin, "CIZ", "porcentajes:inc:7:fin",
                                  "PT26/00251", can=0.0, hmoide=777,
                                  parte_est=est)]


class _CuentaPartes(ClienteInc):
    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.lecturas_partes = 0
        self.codigos_nuevos = 0

    def partes_del_periodo(self, obra_ide, ano, mes):
        self.lecturas_partes += 1
        return super().partes_del_periodo(obra_ide, ano, mes)

    def siguiente_cod_pt(self, ano, empresa=None):
        self.codigos_nuevos += 1
        return super().siguiente_cod_pt(ano, empresa)


def test_f030_r41_preflight_edita_con_la_traza_y_lee_por_ide():
    cli = ClienteInc(existentes=_par_sigrid())
    pf = _pf(cli, [], [_inc_pf(desde=6, **TRAZA)])
    assert [(a.rol, a.accion, a.fecha_int, a.fec_antes, a.hmores_ide,
             a.parte_cod) for a in pf.incidencias] == [
        ("ini", "editar", 20260706, 20260705, 9001, "PT26/00251"),
        ("fin", "ya_registrado", 20260709, None, 9002, "PT26/00251")]
    assert cli.leidas_inc == [([200], 2026, 7, [777])]
    assert cli.leidas_ides == [[9001, 9002]]
    # Sin traza, la lectura no pide ningún `ide`.
    cli = ClienteInc()
    _pf(cli, [], [_inc_pf()])
    assert cli.leidas_ides == [[]]


@pytest.mark.parametrize("pruebas", [True, False])
def test_f030_r33_preflight_el_parte_nuevo_solo_por_las_que_se_escriben(pruebas):
    """Obs. 7: editar y ya registrada no piden parte; en pruebas, el parte
    del periodo se lee una vez para R33 y para el paso 5."""
    cli = _CuentaPartes(parte_existe=False, existentes=_par_sigrid())
    pf = _pf(cli, [], [_inc_pf(desde=6, **TRAZA)],
             obra_pruebas_forzar=pruebas)
    assert [a.accion for a in pf.incidencias] == ["editar", "ya_registrado"]
    assert (pf.partes, cli.codigos_nuevos) == ([], 0)
    assert cli.lecturas_partes == (1 if pruebas else 0)
    cli = _CuentaPartes(parte_existe=False)
    pf = _pf(cli, [linea(registro_id=1)], [_inc_pf()],
             obra_pruebas_forzar=pruebas)
    assert [(p.existe, p.cod) for p in pf.partes] == [(False, "PT26/09999")]
    assert [a.parte_cod for a in pf.incidencias] == ["PT26/09999"] * 2
    assert (cli.lecturas_partes, cli.codigos_nuevos) == (1, 1)


def test_f030_r43_preflight_parte_cerrado_omite():
    from application.services.reglas_incidencias import MOTIVO_INC_CERRADO

    pf = _pf(ClienteInc(existentes=_par_sigrid(est=3)), [],
             [_inc_pf(desde=6, hasta=12, **TRAZA)])
    assert [(a.accion, a.motivo) for a in pf.incidencias] == [
        ("omitir", MOTIVO_INC_CERRADO.format(parte="PT26/00251", desde=5,
                                             hasta=9))] * 2
    assert pf.partes == []


@pytest.mark.parametrize("pruebas", [True, False])
def test_f030_r40_lote_los_ide_en_la_misma_ronda_y_como_suelto(pruebas):
    from interface_adapters.api.app import _respuesta_preflight

    peticiones = [(OBRA, [], [_inc_pf(desde=6, **TRAZA)]),
                  (OBRA_B, [], [_inc_pf(id=8, recurso_ide=400, desde=12,
                                        hasta=14)])]
    cli = ClienteInc(existentes=_par_sigrid())
    lote = _lote(cli, peticiones, obra_pruebas_forzar=pruebas)
    assert cli.leidas_inc == [([200, 400], 2026, 7,
                               [777] if pruebas else None)]
    assert cli.leidas_ides == [[9001, 9002]]
    for r, (obra, lineas, inc) in zip(lote, peticiones):
        suelto = _suelto(ClienteInc(existentes=_par_sigrid()), obra, lineas,
                         inc, obra_pruebas_forzar=pruebas)
        assert _respuesta_preflight(r) == _respuesta_preflight(suelto)
    assert [a.accion for a in lote[0].incidencias] == ["editar",
                                                       "ya_registrado"]
    assert _respuesta_preflight(lote[0])["incidencias"][0]["fec_antes"] \
        == 20260705


def test_f030_r40_lote_sirve_lo_leido_por_ide_y_pide_lo_que_falta():
    from application.services.lecturas_lote import LecturasDelLote

    filas = [LineaIncidenciaSigrid(1, 200, 20260705, "CIV", None, "P"),
             LineaIncidenciaSigrid(2, 400, 20260705, "CIV", None, "P"),
             LineaIncidenciaSigrid(3, 999, 20260605, "CIE", None, "P"),
             LineaIncidenciaSigrid(4, 200, 20260605, "CIV", None, "P"),
             LineaIncidenciaSigrid(5, 200, 20260706, "MENC", None, "P"),
             LineaIncidenciaSigrid(6, 200, 20260731, None, None, "P")]
    cli = ClienteInc(existentes=filas)
    memoria = LecturasDelLote(cli, 2)
    memoria.precargar([(OBRA, [], [_inc_pf(hmores_ide_ini=3, dia_ini=5)]),
                       (OBRA, [], [_inc_pf(id=8, recurso_ide=400)])],
                      _ajustes(obra_pruebas_forzar=False))
    assert (cli.leidas_inc, cli.leidas_ides) == ([([200, 400], 2026, 7, None)],
                                                 [[3]])
    # Del recurso, en el mes y `CI*`; o por su `ide`, esté donde esté.
    assert [x.ide for x in memoria.incidencias_del_mes(
        [200], 2026, 7, ides=[3])] == [1, 3]
    assert [x.ide for x in memoria.incidencias_del_mes([400], 2026, 7)] == [2]
    assert memoria.fallos_de_memoria == {}
    memoria.incidencias_del_mes([200], 2026, 7, ides=[3, 9])
    assert memoria.fallos_de_memoria == {"incidencias_del_mes": 1}
    assert cli.leidas_ides[-1] == [3, 9]


def test_f030_r33_lote_sin_la_linea_larga_de_la_obs_3():
    """Obs. 3 de la review: la condición de `_por_leer_incidencias` partida
    a mano con 25 espacios dentro de la línea."""
    from pathlib import Path

    fuente = (Path(__file__).resolve().parents[1] / "application" / "services"
              / "lecturas_lote.py").read_text(encoding="utf-8")
    assert not [n for n, linea_ in enumerate(fuente.splitlines(), 1)
                if "}" + " " * 10 in linea_]


# =========================== ejecutar (T31) ============================= #
from dataclasses import replace

from domain.models.registro_models import LineaSigrid

from tests.test_f030_pipeline_incidencias import ClienteEscribe, _ej


class _ClienteEdita(ClienteEscribe):
    """El par de la 7 (9001 `CIV` el 5, 9002 `CIZ` el 9) en el parte 777
    En registro. La lectura de R33 sale de esas líneas; `cambios` (por
    `ide`: campos o `None`, borrada) es lo que alguien tocó en Sigrid entre
    el preflight y la relectura de R45. El `UPDATE` de la `fec` lo aplica
    `EdicionesFalsas` (conftest), con su guarda."""

    def __init__(self, cambios=None, **kw) -> None:
        par = [LineaSigrid(9001, 200, 20260705, 71, "CIV", 0.0, 0.0,
                           "porcentajes:inc:7:ini", nuestra=True),
               LineaSigrid(9002, 200, 20260709, 79, "CIZ", 0.0, 0.0,
                           "porcentajes:inc:7:fin", nuestra=True)]
        super().__init__(lineas_parte=par, **kw)
        self.cambios = dict(cambios or {})

    def incidencias_del_mes(self, resides, ano, mes, hmoides=None, ides=()):
        self.leidas_inc.append((sorted(resides), ano, mes, hmoides))
        self.leidas_ides.append(sorted(ides))
        base = int(ano) * 10000 + int(mes) * 100
        return [LineaIncidenciaSigrid(
            ls.ide, ls.reside, ls.fecha_int, ls.hora_codigo, ls.synckey,
            self.parte.cod, can=ls.can, hmoide=int(self.parte.ide),
            parte_est=1) for ls in self.lineas_parte
            if (ls.reside in set(resides) and base < ls.fecha_int <= base + 31)
            or ls.ide in set(ides)]

    def lineas_para_editar(self, ides):
        out = super().lineas_para_editar(ides)
        for ide, kw in self.cambios.items():
            if ide in out and kw is None:
                del out[ide]
            elif ide in out:
                out[ide] = replace(out[ide], **kw)
        return out

    def lineas_registradas(self, claves, ides=()):
        self.lineas_registradas_pedidas = [
            *getattr(self, "lineas_registradas_pedidas", []),
            sorted(int(i) for i in ides if i)]
        return super().lineas_registradas(claves, ides)

    def dias(self):
        return [(ls.ide, ls.fecha_int) for ls in self.lineas_parte]


def _acc(res):
    return [(a.rol, a.accion, a.fecha_int, a.fec_antes, a.hmores_ide,
             a.parte_cod) for a in res.incidencias]


def test_f030_r41_ejecutar_edita_el_par_en_su_sitio_y_nada_mas():
    cli = _ClienteEdita()
    res = _ej(cli, [], [_inc_pf(desde=6, hasta=12, **TRAZA)])
    assert [s["sql"] for s in cli.escritos] == ["editar_fec", "editar_fec"]
    assert [s["parameters"] for s in cli.escritos] == [
        {"ide": 9001, "reside": 200, "hora_codigo": "CIV",
         "synckey_leida": "porcentajes:inc:7:ini", "fecha_int": 20260706},
        {"ide": 9002, "reside": 200, "hora_codigo": "CIZ",
         "synckey_leida": "porcentajes:inc:7:fin", "fecha_int": 20260712}]
    assert cli.dias() == [(9001, 20260706), (9002, 20260712)]
    assert _acc(res) == [
        ("ini", "editar", 20260706, 20260705, 9001, "PT26/00251"),
        ("fin", "editar", 20260712, 20260709, 9002, "PT26/00251")]
    assert [a.motivo for a in res.incidencias] == [None, None]
    assert cli.para_editar == [[9001, 9002]]       # UNA relectura (R45)
    assert (cli.inserts(), res.partes, res.escritas) == ([], [], [])


def test_f030_r41_ejecutar_con_lineas_una_sola_relectura_y_juntas():
    cli = _ClienteEdita()
    res = _ej(cli, [linea(registro_id=1)], [_inc_pf(desde=6, **TRAZA)])
    assert [s["sql"] for s in cli.escritos] == ["insert", "editar_fec"]
    assert cli.para_editar == [[9001]]
    assert [a.accion for a in res.incidencias] == ["editar", "ya_registrado"]
    assert cli.dias() == [(9001, 20260706), (9002, 20260709)]


@pytest.mark.parametrize("cambio", [
    {"can": 1.0}, {"fecha_int": 20260707},
    {"hora_codigo": "CIE"}, {"synckey": "porcentajes:inc:8:fin"},
    {"reside": 201}, {"enlazada": True}, {"parte_est": 3}, None])
def test_f030_r45_si_una_del_par_ya_no_vale_no_se_edita_ninguna(cambio):
    from application.services.reglas_incidencias import (
        MOTIVO_INC_CAMBIADA,
        MOTIVO_INC_PAR,
    )

    cli = _ClienteEdita(cambios={9002: cambio})
    res = _ej(cli, [], [_inc_pf(desde=6, hasta=12, **TRAZA)])
    assert cli.escritos == []
    assert cli.dias() == [(9001, 20260705), (9002, 20260709)]
    assert [(a.accion, a.fec_antes, a.hmores_ide, a.motivo)
            for a in res.incidencias] == [
        ("omitir", None, 9001, MOTIVO_INC_PAR.format(ide=9002)),
        ("omitir", None, 9002, MOTIVO_INC_CAMBIADA.format(ide=9002))]


def test_f030_r45_can_nulo_en_la_relectura_cuenta_como_cero():
    cli = _ClienteEdita(cambios={9002: {"can": None}})
    res = _ej(cli, [], [_inc_pf(desde=6, hasta=12, **TRAZA)])
    assert [a.accion for a in res.incidencias] == ["editar", "editar"]


def test_f030_r45_la_que_no_se_edita_no_arrastra_a_la_ya_registrada():
    from application.services.reglas_incidencias import MOTIVO_INC_CAMBIADA

    cli = _ClienteEdita(cambios={9001: {"can": 2.0}})
    res = _ej(cli, [linea(registro_id=1)], [_inc_pf(desde=6, **TRAZA)])
    assert [s["sql"] for s in cli.escritos] == ["insert"]
    assert [(a.accion, a.motivo) for a in res.incidencias] == [
        ("omitir", MOTIVO_INC_CAMBIADA.format(ide=9001)),
        ("ya_registrado", ("ya registrada en Sigrid (línea 9002); no se "
                           "duplica"))]


def test_f030_r45_si_la_guarda_no_la_cambia_va_a_omitir_y_no_se_inserta():
    from application.services.reglas_incidencias import MOTIVO_INC_CAMBIADA

    cli = _ClienteEdita()
    cli.guarda_falla = frozenset({9001})
    res = _ej(cli, [], [_inc_pf(desde=6, hasta=12, **TRAZA)])
    assert [s["sql"] for s in cli.escritos] == ["editar_fec", "editar_fec"]
    assert cli.dias() == [(9001, 20260705), (9002, 20260712)]
    assert [(a.accion, a.fec_antes, a.motivo) for a in res.incidencias] == [
        ("omitir", None, MOTIVO_INC_CAMBIADA.format(ide=9001)),
        ("editar", 20260709, None)]
    assert cli.inserts() == []
    # La relectura de lo escrito pide los `ide` editados (F-051 R15).
    assert cli.lineas_registradas_pedidas[-1] == [9001, 9002]


def test_f030_r46_el_log_de_cada_edicion(caplog):
    import logging

    caplog.set_level(logging.INFO)
    _ej(_ClienteEdita(), [], [_inc_pf(desde=6, **TRAZA)])
    lineas = [r.getMessage() for r in caplog.records
              if "edita fec" in r.getMessage()]
    assert len(lineas) == 1
    msg = lineas[0]
    for trozo in ("ide=9001", "parte=PT26/00251", "incidencia=7", "rol=ini",
                  "'fecha_int': 20260705", "'synckey': 'porcentajes:inc:7:ini'",
                  "'can': 0.0", "'hora_codigo': 'CIV'", "fec=20260706"):
        assert trozo in msg, trozo


def test_f030_r41_ejecutar_repetido_no_hace_nada():
    cli = _ClienteEdita()
    _ej(cli, [], [_inc_pf(desde=6, hasta=12, **TRAZA)])
    traza = {**TRAZA, "dia_ini": 6, "dia_fin": 12}
    res = _ej(cli, [], [_inc_pf(desde=6, hasta=12, **traza)])
    assert len(cli.escritos) == 2
    assert [a.accion for a in res.incidencias] == ["ya_registrado"] * 2
