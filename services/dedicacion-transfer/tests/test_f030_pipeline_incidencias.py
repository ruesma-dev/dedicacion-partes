# tests/test_f030_pipeline_incidencias.py
"""F-030 · Las incidencias en el registro: cliente, pipeline, lote, contrato
y script (R23-R33, R35; ARCHITECTURE.md#regla-incidencia).

Sin red ni BBDD: el cliente de Sigrid con su `_read` sustituido por un doble
y el pipeline con el `ClienteFalso` de `conftest.py`. Los `ide` son
inventados y no coinciden con ningún dato real.
"""
from __future__ import annotations

from dataclasses import asdict

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.reglas_incidencias import (
    MOTIVO_INC_DUPLICADA,
    MOTIVO_INC_SIN_CODIGO,
)
from application.services.reglas_porcentajes import (
    MOTIVO_EMPRESA_OBRA,
    MOTIVO_SIN_EMPRESA,
    EmpresasMezcladas,
)
from domain.models.registro_models import (
    HoraRecurso,
    IncidenciaEntrada,
    LineaIncidenciaSigrid,
    ObraEntrada,
)

from tests.conftest import (
    EMPRESA,
    OBRA_ORIGEN,
    ClienteFalso,
    SettingsFalso,
    linea,
    linea_previa,
)
from tests.test_f050_propuesta import _cliente_historial

# ============================ cliente (T12) ============================== #
FILA_INC = {"ide": 900, "reside": 200, "fec": 20260705, "cod": "CIV ",
            "synckey": " porcentajes:inc:7:ini ", "parte": "PT26/00012"}


def test_f030_r27_cliente_sql_parametros_y_mapeo():
    cli, falso = _cliente_historial([FILA_INC, dict(FILA_INC, ide=901, synckey=None,
                                                    cod=None, parte=None)])
    filas = cli.incidencias_del_mes([300, 200, 300, None, 0], 2026, 2)
    [(sql, params)] = falso.llamadas
    assert sql == (
        "SELECT h.ide AS ide, h.reside AS reside, h.fec AS fec, a.cod AS cod, "
        "h.synckey AS synckey, c.cod AS parte FROM hmores h "
        "JOIN auxhor a ON a.ide = h.horide JOIN hmo m ON m.ide = h.hmoide "
        "JOIN con c ON c.ide = m.ide WHERE h.reside IN (?,?) "
        "AND h.fec BETWEEN ? AND ? AND a.cod LIKE ? ORDER BY h.ide")
    assert params == [200, 300, 20260201, 20260228, "CI%"]
    assert filas == [
        LineaIncidenciaSigrid(ide=900, reside=200, fecha_int=20260705,
                              hora_codigo="CIV", synckey="porcentajes:inc:7:ini",
                              parte_cod="PT26/00012"),
        LineaIncidenciaSigrid(ide=901, reside=200, fecha_int=20260705,
                              hora_codigo=None, synckey=None, parte_cod=None)]


def test_f030_r27_cliente_en_pruebas_solo_los_partes_dados():
    cli, falso = _cliente_historial()
    cli.incidencias_del_mes([200], 2026, 7, hmoides=[12, 11, 12])
    [(sql, params)] = falso.llamadas
    assert sql.endswith("AND a.cod LIKE ? AND h.hmoide IN (?,?) ORDER BY h.ide")
    assert params == [200, 20260701, 20260731, "CI%", 11, 12]


def test_f030_r33_cliente_sin_recursos_o_sin_partes_no_lee():
    cli, falso = _cliente_historial([FILA_INC])
    assert cli.incidencias_del_mes([None, 0], 2026, 7) == []
    assert cli.incidencias_del_mes([200], 2026, 7, hmoides=[]) == []
    assert cli.incidencias_del_mes([200], 2026, 7, hmoides=[0, None]) == []
    assert falso.llamadas == []


def test_f030_r33_cliente_en_trozos_de_500_recursos():
    cli, falso = _cliente_historial([FILA_INC])
    filas = cli.incidencias_del_mes(range(1, 1202), 2026, 7)
    assert [len(p) for _, p in falso.llamadas] == [503, 503, 204]   # + 3 fijos
    assert [p[0] for _, p in falso.llamadas] == [1, 501, 1001]
    assert len(filas) == 3
    cli, falso = _cliente_historial()
    cli.incidencias_del_mes(range(1, 501), 2026, 7)
    assert len(falso.llamadas) == 1


def test_f030_r33_cliente_truncado_es_error(monkeypatch):
    from tests.test_f047_tope_filas import _cliente as cliente_emulado
    from tests.test_f047_tope_filas import _emulada

    _emulada(monkeypatch, [dict(FILA_INC), dict(FILA_INC, ide=99)])
    with pytest.raises(RuntimeError, match="truncada"):
        cliente_emulado(max_rows=1).incidencias_del_mes([200], 2026, 7)


def test_f030_r33_cliente_se_mide_con_su_nombre():
    from infrastructure.sigrid.sigrid_write_client import medir_lecturas

    cli, _ = _cliente_historial()
    with medir_lecturas() as m:
        cli.incidencias_del_mes([1], 2026, 7)
    assert [l.nombre for l in m.lecturas] == ["incidencias_del_mes"]


# ============================ pipeline (T13) ============================= #
OBRA = ObraEntrada(codigo=OBRA_ORIGEN)


class ClienteInc(ClienteFalso):
    """El doble de `conftest.py` con las horas de incidencia (`CIV`, `CIZ`)
    en los recursos 200 y 400 (el 300 no las tiene; el `CIV` del 200 con su
    cuenta de plantilla) y la lectura de R27, que anota cada llamada y
    devuelve ``existentes`` (o lanza ``falla``)."""

    def __init__(self, *, existentes=(), falla=None, **kw) -> None:
        super().__init__(**kw)
        for r in (200, 400):
            self.horas[r] = [*self.horas[r],
                             HoraRecurso(71, "CIV", "Vacaciones(V)", 12.5,
                                         caa_cod=("00000.CIMO07" if r == 200
                                                  else None)),
                             HoraRecurso(79, "CIZ", "Fin de Incidencia", 0.0)]
        self.existentes_inc = list(existentes)
        self.falla = falla
        self.leidas_inc: list[tuple] = []
        self.leidas_horas: list[list[int]] = []

    def horas_de_recursos(self, resides):
        self.leidas_horas.append(sorted(resides))
        return super().horas_de_recursos(resides)

    def incidencias_del_mes(self, resides, ano, mes, hmoides=None):
        self.leidas_inc.append((sorted(resides), ano, mes, hmoides))
        if self.falla is not None:
            raise self.falla
        return list(self.existentes_inc)


def _inc(**kw) -> IncidenciaEntrada:
    base = {"id": 7, "recurso_ide": 200, "empresa": EMPRESA, "codigo": "CIV",
            "ano": 2026, "mes": 7, "desde": 5, "hasta": 9, "paride": 0}
    base.update(kw)
    return IncidenciaEntrada(**base)


def _pf(cli, lineas=(), incidencias=None, *, obra=OBRA, **ajustes):
    pipe = RegistroPipeline(cliente=cli, settings=SettingsFalso(**ajustes))
    if incidencias is None:
        return pipe.preflight(obra=obra, lineas=list(lineas))
    return pipe.preflight(obra=obra, lineas=list(lineas),
                          incidencias=list(incidencias))


def _resumen(pf):
    return [(a.id, a.rol, a.accion, a.fecha_int, a.hora_codigo, a.parte_cod,
             a.motivo) for a in pf.incidencias]


def test_f030_r24_preflight_par_en_el_parte_del_periodo_con_su_cuenta():
    cli = ClienteInc()
    pf = _pf(cli, [linea(registro_id=1)], [_inc(paride=80001)])
    assert _resumen(pf) == [
        (7, "ini", "escribir", 20260705, "CIV", "PT26/00251", None),
        (7, "fin", "escribir", 20260709, "CIZ", "PT26/00251", None)]
    ini, fin = pf.incidencias
    assert (ini.hora_ide, ini.pre, fin.hora_ide, fin.pre) == (71, 12.5, 79, 0.0)
    assert (ini.paride, fin.paride) == (80001, 80001)
    # Cuenta analítica como cualquier línea (en el centro de la obra destino,
    # la de pruebas): la plantilla de su hora; el CIZ no tiene, ni su
    # partida (el doble no da cuenta de partida): 0.
    assert (ini.caa_cod, ini.caa_origen) == ("0404.CIMO07", "recurso")
    assert ini.caa_ide > 0
    assert (fin.caa_ide, fin.caa_cod) == (0, None)
    assert pf.acciones[0].caa_cod == "0404.CIMO03"
    assert len(pf.partes) == 1


def test_f030_r2_preflight_las_lineas_deciden_igual_con_y_sin_incidencias():
    lineas = [linea(registro_id=1), linea(registro_id=2, recurso_ide=400),
              linea(registro_id=3, recurso_ide=300)]
    previas = [linea_previa(),
               linea_previa(ide=5002, reside=200, horide=71,
                            hora_codigo="CIV", can=0.0, tot=0.0,
                            fecha_int=20260705)]
    sin = _pf(ClienteInc(lineas_parte=previas), lineas)
    con = _pf(ClienteInc(lineas_parte=previas), lineas,
              [_inc(), _inc(id=8, recurso_ide=400, desde=1, hasta=31)])
    assert [asdict(a) for a in con.acciones] == [asdict(a) for a in sin.acciones]
    assert [asdict(c) for c in con.conflictos] == [
        asdict(c) for c in sin.conflictos]
    assert [asdict(p) for p in con.partes] == [asdict(p) for p in sin.partes]
    assert sin.incidencias == []
    assert [a.accion for a in con.incidencias] == ["escribir"] * 4
    # R28: ninguna incidencia es conflicto (ni pisado, ni sobrecarga, ni
    # sin partida), aunque el recurso tenga su M* en el mismo parte.
    assert con.conflictos
    assert all(set(c.registros) <= {1, 2, 3} for c in con.conflictos)


def test_f030_r28_preflight_sin_partida_no_es_conflicto():
    pf = _pf(ClienteInc(), [], [_inc(paride=0)])
    assert pf.conflictos == [] and pf.acciones == []
    assert [(a.accion, a.paride) for a in pf.incidencias] == [
        ("escribir", 0)] * 2


def test_f030_r23_preflight_obra_solo_con_incidencias():
    cli = ClienteInc(parte_existe=False)
    pf = _pf(cli, [], [_inc()])
    assert pf.acciones == []
    assert [(p.existe, p.cod) for p in pf.partes] == [(False, "PT26/09999")]
    assert _resumen(pf)[0][2:6] == ("escribir", 20260705, "CIV", "PT26/09999")
    assert cli.leidas_horas == [[200]]


def test_f030_r23_preflight_sin_empresa_se_omite_sin_leer():
    cli = ClienteInc()
    pf = _pf(cli, [], [_inc(empresa=None)])
    assert [(a.accion, a.motivo) for a in pf.incidencias] == [
        ("omitir", MOTIVO_SIN_EMPRESA)] * 2
    assert cli.leidas_inc == [] and cli.leidas_horas == []
    assert pf.partes == []


def test_f030_r23_preflight_obra_de_otra_empresa():
    cli = ClienteInc()
    pf = _pf(cli, [], [_inc(empresa=2)], obra=ObraEntrada(ide=828942))
    motivo = MOTIVO_EMPRESA_OBRA.format(cod="0404", emp_obra=1, emp_linea=2)
    assert [(a.accion, a.motivo) for a in pf.incidencias] == [
        ("omitir", motivo)] * 2
    assert cli.leidas_inc == [] and cli.leidas_horas == []


def test_f030_r23_preflight_una_empresa_por_peticion():
    with pytest.raises(EmpresasMezcladas):
        _pf(ClienteInc(), [linea(registro_id=1)], [_inc(empresa=2)])
    pf = _pf(ClienteInc(), [linea(registro_id=1, empresa=None)], [_inc()])
    assert (pf.acciones[0].accion, pf.acciones[0].motivo) == (
        "omitir", MOTIVO_SIN_EMPRESA)
    assert [a.accion for a in pf.incidencias] == ["escribir"] * 2


def test_f030_r26_preflight_recurso_sin_codigos_no_lee_r27():
    cli = ClienteInc()
    pf = _pf(cli, [], [_inc(recurso_ide=300)])
    assert [(a.accion, a.motivo) for a in pf.incidencias] == [
        ("omitir", MOTIVO_INC_SIN_CODIGO.format(cod="CIV"))] * 2
    assert cli.leidas_inc == []
    assert pf.partes == []


def test_f030_r27_preflight_duplicada_en_otro_parte_y_modo_pruebas():
    otra = LineaIncidenciaSigrid(ide=61, reside=200, fecha_int=20260709,
                                 hora_codigo="CIZ", synckey=None,
                                 parte_cod="PT26/00041")
    cli = ClienteInc(existentes=[otra])
    pf = _pf(cli, [linea(registro_id=1)], [_inc()])
    assert _resumen(pf) == [
        (7, "ini", "escribir", 20260705, "CIV", "PT26/00251", None),
        (7, "fin", "omitir", 20260709, "CIZ", "PT26/00041",
         MOTIVO_INC_DUPLICADA.format(cod="CIZ", dia=9, mes=7,
                                     parte="PT26/00041"))]
    # En pruebas, solo los partes del periodo de la obra de pruebas.
    assert cli.leidas_inc == [([200], 2026, 7, [777])]


def test_f030_r27_preflight_en_real_todas_las_obras():
    cli = ClienteInc()
    _pf(cli, [], [_inc()], obra_pruebas_forzar=False)
    assert cli.leidas_inc == [([200], 2026, 7, None)]


def test_f030_r27_preflight_en_pruebas_sin_partes_no_hay_duplicado():
    cli = ClienteInc(parte_existe=False, existentes=[])
    pf = _pf(cli, [], [_inc()])
    assert [a.accion for a in pf.incidencias] == ["escribir", "escribir"]
    assert cli.leidas_inc == [([200], 2026, 7, [])]


def test_f030_r33_preflight_una_lectura_por_peticion_y_solo_con_incidencias():
    cli = ClienteInc()
    _pf(cli, [linea(registro_id=1)])
    _pf(cli, [linea(registro_id=1)], [])
    assert cli.leidas_inc == []
    _pf(cli, [], [_inc(), _inc(id=8, recurso_ide=400, desde=12, hasta=12),
                  _inc(id=9, recurso_ide=300)])
    assert cli.leidas_inc == [([200, 400], 2026, 7, [777])]


def test_f030_r33_preflight_si_la_lectura_falla_la_peticion_falla():
    cli = ClienteInc(falla=RuntimeError("lectura truncada"))
    with pytest.raises(RuntimeError, match="truncada"):
        _pf(cli, [linea(registro_id=1)], [_inc()])


def test_f030_r25_preflight_la_partida_se_valida_por_ide():
    cli = ClienteInc()
    pf = _pf(cli, [linea(registro_id=1, paride=80002, partida_cod="CI.1.20")],
             [_inc(paride=80001), _inc(id=8, recurso_ide=400, paride=70001)])
    assert [(a.accion, a.paride, a.motivo) for a in pf.incidencias] == [
        ("escribir", 80001, None)] * 2 + [("escribir", 0, None)] * 2
    assert cli.validadas == [[70001, 80001, 80002]]   # una sola lectura


# ============================ ejecutar (T14) ============================= #
class ClienteEscribe(ClienteInc):
    """`ClienteInc` que «escribe»: el alta deja el parte En registro y cada
    INSERT queda localizable por su `synckey`, como en Sigrid."""

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self._siguiente = 70000

    def escribir(self, statements):
        from domain.models.registro_models import LineaSigrid

        n = super().escribir(statements)
        for s in statements:
            kw = s["parameters"]
            if s["sql"] == "crear":
                self.parte.existe, self.parte.ide = True, 778
                self.parte.cod = kw["cod"]
            elif s["sql"] == "insert":
                self._siguiente += 1
                self.synckeys[kw["synckey"]] = LineaSigrid(
                    ide=self._siguiente, reside=kw["reside"],
                    fecha_int=kw["fecha_int"], horide=kw["horide"],
                    hora_codigo=None, can=kw["can"], tot=None,
                    synckey=kw["synckey"], nuestra=True)
        return n


def _ej(cli, lineas=(), incidencias=None, *, pisar=None, **ajustes):
    pipe = RegistroPipeline(cliente=cli, settings=SettingsFalso(**ajustes))
    kw = {} if incidencias is None else {"incidencias": list(incidencias)}
    return pipe.ejecutar(obra=OBRA, lineas=list(lineas), pisar_claves=pisar,
                         **kw)


def _sin_pos(inserts):
    return [{k: v for k, v in i.items() if k != "obra"} for i in inserts]


def test_f030_r24_ejecutar_inserta_el_par_con_can_cero_tras_las_lineas():
    cli = ClienteEscribe()
    res = _ej(cli, [linea(registro_id=1)], [_inc(paride=80001)])
    linea_m, ini, fin = _sin_pos(cli.inserts())
    assert linea_m["synckey"] == "porcentajes:1"
    assert (ini["pos"], fin["pos"]) == (linea_m["pos"] + 64, linea_m["pos"] + 128)
    for ins, rol, fec, horide, pre in ((ini, "ini", 20260705, 71, 12.5),
                                       (fin, "fin", 20260709, 79, 0.0)):
        assert ins == {
            "hmoide": 777, "reside": 200, "pos": ins["pos"],
            "fecha_int": fec, "horide": horide, "can": 0.0, "pre": pre,
            "ano": 2026, "mes": 7, "synckey": f"porcentajes:inc:7:{rol}",
            "tex": "PRUEBA-PORC", "paride": 80001,
            "caaide": ins["caaide"]}
    assert ini["caaide"] > 0 and fin["caaide"] == 0
    # Las incidencias no son `escritas` (eso es de las asignaciones).
    assert [e["registro_id"] for e in res.escritas] == [1]
    assert [(a.rol, a.accion, a.hmores_ide, a.parte_cod)
            for a in res.incidencias] == [
        ("ini", "escribir", 70002, "PT26/00251"),
        ("fin", "escribir", 70003, "PT26/00251")]


def test_f030_r24_ejecutar_con_el_cliente_real_tot_cero():
    from infrastructure.sigrid.sigrid_write_client import SigridWriteClient

    cli = SigridWriteClient(base_url="http://sigrid.invalid",
                            function_key="sin-clave", database="ruesma")
    obra = ObraEntrada(ide=5, codigo="0404")
    obra.cenide = 6
    st = cli.stmt_insert_linea(hmoide=1, obra=obra, reside=200, pos=64,
                               fecha_int=20260705, horide=71, can=0.0,
                               pre=12.5, ano=2026, mes=7,
                               synckey="porcentajes:inc:7:ini", tex=None)
    assert st["parameters"][8:11] == [0.0, 12.5, 0.0]       # can, pre, tot


def test_f030_r2_ejecutar_las_lineas_se_escriben_igual():
    lineas = [linea(registro_id=1), linea(registro_id=2, recurso_ide=400)]
    sin, con = ClienteEscribe(), ClienteEscribe()
    r_sin = _ej(sin, lineas)
    r_con = _ej(con, lineas, [_inc(), _inc(id=8, recurso_ide=400)])
    assert con.inserts()[:2] == sin.inserts()
    assert [i["synckey"] for i in con.inserts()[2:]] == [
        "porcentajes:inc:7:ini", "porcentajes:inc:7:fin",
        "porcentajes:inc:8:ini", "porcentajes:inc:8:fin"]
    assert r_con.escritas == r_sin.escritas and r_sin.incidencias == []
    assert (r_con.omitidas, r_con.ya_registradas) == (
        r_sin.omitidas, r_sin.ya_registradas)


def test_f030_r23_ejecutar_obra_solo_con_incidencias_crea_el_parte():
    cli = ClienteEscribe(parte_existe=False)
    res = _ej(cli, [], [_inc()])
    assert [s["sql"] for s in cli.escritos] == ["crear", "insert", "insert"]
    assert {i["hmoide"] for i in cli.inserts()} == {778}
    assert [a.parte_cod for a in res.incidencias] == ["PT26/09999"] * 2
    assert res.partes[0].creado is True


def test_f030_r28_ejecutar_un_conflicto_sin_confirmar_no_las_retiene():
    cli = ClienteEscribe(lineas_parte=[linea_previa()])
    res = _ej(cli, [linea(registro_id=1)], [_inc()])
    assert res.pendientes_confirmacion and res.escritas == []
    assert [i["synckey"] for i in cli.inserts()] == [
        "porcentajes:inc:7:ini", "porcentajes:inc:7:fin"]
    assert cli.borrados() == []


def test_f030_r30_ejecutar_no_reescribe_la_ya_registrada():
    # La 7 ya se registró del 5 al 9; ahora llega del 6 al 9.
    ya = [LineaIncidenciaSigrid(51, 200, 20260705, "CIV",
                                "porcentajes:inc:7:ini", "PT26/00251"),
          LineaIncidenciaSigrid(52, 200, 20260709, "CIZ",
                                "porcentajes:inc:7:fin", "PT26/00251")]
    cli = ClienteEscribe(existentes=ya)
    res = _ej(cli, [], [_inc(desde=6)])
    assert cli.inserts() == []
    assert [(a.rol, a.accion, a.hmores_ide, a.parte_cod)
            for a in res.incidencias] == [
        ("ini", "ya_registrado", 51, "PT26/00251"),
        ("fin", "ya_registrado", 52, "PT26/00251")]
    # Repetir ejecutar con lo mismo: tampoco.
    res = _ej(cli, [], [_inc()])
    assert cli.inserts() == []
    assert [a.accion for a in res.incidencias] == ["ya_registrado"] * 2


def test_f030_r27_ejecutar_omitidas_no_se_escriben():
    otra = LineaIncidenciaSigrid(61, 200, 20260705, "CIV", None, "PT26/00041")
    cli = ClienteEscribe(existentes=[otra])
    res = _ej(cli, [], [_inc(), _inc(id=9, recurso_ide=300)])
    assert [i["synckey"] for i in cli.inserts()] == ["porcentajes:inc:7:fin"]
    assert [a.accion for a in res.incidencias] == [
        "omitir", "escribir", "omitir", "omitir"]


def test_f030_r33_ejecutar_si_la_lectura_falla_no_escribe_nada():
    cli = ClienteEscribe(falla=RuntimeError("lectura truncada"))
    with pytest.raises(RuntimeError, match="truncada"):
        _ej(cli, [linea(registro_id=1)], [_inc()])
    assert cli.escritos == []


def test_f030_r29_ejecutar_fuera_de_pruebas_sin_marca():
    cli = ClienteEscribe()
    _ej(cli, [], [_inc()], obra_pruebas_forzar=False)
    assert {i["tex"] for i in cli.inserts()} == {None}
    assert {i["hmoide"] for i in cli.inserts()} == {777}


def test_f030_r28_ejecutar_una_linea_de_incidencia_no_es_linea_al_cero():
    """Con F-051: una línea `CI*`/`CIZ` del recurso (siempre `can = 0`) no
    es «la línea al 0 %» que se edita en su sitio; esa es solo `M*`."""
    civ = linea_previa(ide=5002, horide=71, hora_codigo="CIV", can=0.0,
                       tot=0.0, fecha_int=20260705)
    ciz = linea_previa(ide=5003, horide=79, hora_codigo="CIZ", can=None,
                       tot=0.0, fecha_int=20260709)
    cli = ClienteEscribe(lineas_parte=[civ, ciz])
    res = _ej(cli, [linea(registro_id=1)], [_inc(id=8, desde=12, hasta=14)])
    assert res.editadas == [] and res.a_cero == [] and res.pendientes_confirmacion == []
    assert [s["sql"] for s in cli.escritos] == ["insert"] * 3
    assert [i["synckey"] for i in cli.inserts()] == [
        "porcentajes:1", "porcentajes:inc:8:ini", "porcentajes:inc:8:fin"]
