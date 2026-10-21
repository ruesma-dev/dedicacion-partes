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
    OBRA_SIN_PARTIDA_PV,
    ClienteFalso,
    SettingsFalso,
    linea,
    linea_previa,
)
from tests.test_f050_propuesta import _cliente_historial

# ============================ cliente (T12) ============================== #
# Anexo R30 (design §13.7): la lectura trae además `can`, parte y estado.
FILA_INC = {"ide": 900, "reside": 200, "fec": 20260705, "cod": "CIV ",
            "synckey": " porcentajes:inc:7:ini ", "parte": "PT26/00012",
            "can": 0, "hmoide": 777, "est": 1}


def test_f030_r27_cliente_sql_parametros_y_mapeo():
    cli, falso = _cliente_historial([FILA_INC, dict(FILA_INC, ide=901, synckey=None,
                                                    cod=None, parte=None)])
    filas = cli.incidencias_del_mes([300, 200, 300, None, 0], 2026, 2)
    [(sql, params)] = falso.llamadas
    assert sql == (
        "SELECT h.ide AS ide, h.reside AS reside, h.fec AS fec, a.cod AS cod, "
        "h.synckey AS synckey, c.cod AS parte, "
        "h.can AS can, h.hmoide AS hmoide, c.est AS est FROM hmores h "
        "JOIN auxhor a ON a.ide = h.horide JOIN hmo m ON m.ide = h.hmoide "
        "JOIN con c ON c.ide = m.ide WHERE h.reside IN (?,?) "
        "AND h.fec BETWEEN ? AND ? AND a.cod LIKE ? ORDER BY h.ide")
    assert params == [200, 300, 20260201, 20260228, "CI%"]
    assert filas == [
        LineaIncidenciaSigrid(ide=900, reside=200, fecha_int=20260705,
                              hora_codigo="CIV", synckey="porcentajes:inc:7:ini",
                              parte_cod="PT26/00012", can=0.0, hmoide=777,
                              parte_est=1),
        LineaIncidenciaSigrid(ide=901, reside=200, fecha_int=20260705,
                              hora_codigo=None, synckey=None, parte_cod=None,
                              can=0.0, hmoide=777, parte_est=1)]


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
    # Anexo R30 (design §13.7): el doble repite la misma fila en cada trozo
    # y cada línea sale una vez (con `ides` una puede salir en dos trozos).
    assert len(filas) == 1
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
    devuelve ``existentes`` (o lanza ``falla``). Anexo R30 (design §13.7):
    acepta los `ides` de la traza y los anota aparte, en ``leidas_ides``."""

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
        self.leidas_ides: list[list[int]] = []
        self.leidas_horas: list[list[int]] = []

    def horas_de_recursos(self, resides):
        self.leidas_horas.append(sorted(resides))
        return super().horas_de_recursos(resides)

    def incidencias_del_mes(self, resides, ano, mes, hmoides=None, ides=()):
        self.leidas_inc.append((sorted(resides), ano, mes, hmoides))
        self.leidas_ides.append(sorted(ides))
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
    # La 7 ya se registró del 5 al 9; ahora llega del 6 al 9. Anexo R30
    # (R41, R45, design §13.7): su `ini` ya no es `ya_registrado` sino
    # `editar`: un `UPDATE` de su `fec`, sin insertar nada. Las líneas
    # leídas traen ya `can` y estado, y el par está en el parte (relectura).
    from domain.models.registro_models import LineaSigrid

    ya = [LineaIncidenciaSigrid(51, 200, 20260705, "CIV",
                                "porcentajes:inc:7:ini", "PT26/00251",
                                can=0.0, hmoide=777, parte_est=1),
          LineaIncidenciaSigrid(52, 200, 20260709, "CIZ",
                                "porcentajes:inc:7:fin", "PT26/00251",
                                can=0.0, hmoide=777, parte_est=1)]
    par = [LineaSigrid(x.ide, 200, x.fecha_int, None, x.hora_codigo, 0.0,
                       0.0, x.synckey) for x in ya]
    cli = ClienteEscribe(existentes=ya, lineas_parte=par)
    res = _ej(cli, [], [_inc(desde=6)])
    assert cli.inserts() == []
    assert [(s["sql"], s["parameters"]["ide"]) for s in cli.escritos] == [
        ("editar_fec", 51)]
    assert [(a.rol, a.accion, a.hmores_ide, a.parte_cod)
            for a in res.incidencias] == [
        ("ini", "editar", 51, "PT26/00251"),
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


# ============================== lote (T15) =============================== #
from application.pipelines.registro_lote import RegistroLote

OBRA_B = ObraEntrada(codigo=OBRA_SIN_PARTIDA_PV)


def _ajustes(**kw):
    st = SettingsFalso(**kw)
    st.sigrid_lecturas_paralelas = 4
    return st


def _lote(cli, peticiones, **kw):
    return RegistroLote(cliente=cli, settings=_ajustes(**kw)).preflight(
        peticiones)


def _suelto(cli, obra, lineas, incidencias, **kw):
    return RegistroPipeline(cliente=cli, settings=_ajustes(**kw)).preflight(
        obra=obra, lineas=lineas, incidencias=incidencias)


def _peticiones():
    return [
        (OBRA, [linea(registro_id=1)], [_inc(paride=80001)]),
        (OBRA_B, [], [_inc(id=8, recurso_ide=400, desde=12, hasta=14)]),
        (OBRA, [linea(registro_id=3, recurso_ide=400)]),
    ]


@pytest.mark.parametrize("pruebas", [True, False])
def test_f030_r33_lote_una_lectura_y_lo_mismo_que_suelto(pruebas):
    from interface_adapters.api.app import _respuesta_preflight

    otra = LineaIncidenciaSigrid(61, 400, 20260714, "CIZ", None, "PT26/00041")
    cli = ClienteInc(existentes=[otra])
    lote = _lote(cli, _peticiones(), obra_pruebas_forzar=pruebas)
    assert cli.leidas_inc == [([200, 400], 2026, 7,
                               [777] if pruebas else None)]
    for r, p in zip(lote, _peticiones()):
        obra, lineas, *inc = p
        suelto = _suelto(ClienteInc(existentes=[otra]), obra, lineas,
                         inc[0] if inc else None,
                         obra_pruebas_forzar=pruebas)
        assert _respuesta_preflight(r) == _respuesta_preflight(suelto)
    assert [a.accion for a in lote[1].incidencias] == ["escribir", "omitir"]
    assert lote[2].incidencias == []


def test_f030_r33_lote_sin_incidencias_no_lee():
    cli = ClienteInc()
    _lote(cli, [(OBRA, [linea(registro_id=1)]),
                (OBRA, [linea(registro_id=2)], [])])
    assert cli.leidas_inc == []


def test_f030_r33_lote_solo_si_alguna_se_escribiria():
    cli = ClienteInc()
    lote = _lote(cli, [(OBRA, [], [_inc(recurso_ide=300)]),
                       (OBRA_B, [], [_inc(id=9, empresa=None)])])
    assert cli.leidas_inc == []
    assert [a.accion for r in lote for a in r.incidencias] == ["omitir"] * 4


def test_f030_r33_lote_si_la_lectura_falla_falla_el_lote():
    cli = ClienteInc(falla=RuntimeError("lectura truncada"))
    with pytest.raises(RuntimeError, match="truncada"):
        _lote(cli, _peticiones())


def test_f030_r33_lote_lo_que_no_se_precargo_va_al_cliente():
    from application.services.lecturas_lote import LecturasDelLote

    cli = ClienteInc()
    memoria = LecturasDelLote(cli, 2)
    memoria.precargar([(OBRA, [], [_inc()])], _ajustes())
    assert cli.leidas_inc == [([200], 2026, 7, [777])]
    assert memoria.incidencias_del_mes([200], 2026, 7, hmoides=[777]) == []
    assert memoria.fallos_de_memoria == {}
    for args, kw in ((([200, 400], 2026, 7), {"hmoides": [777]}),
                     (([200], 2026, 8), {"hmoides": [777]}),
                     (([200], 2026, 7), {"hmoides": [778]}),
                     (([200], 2026, 7), {})):
        memoria.incidencias_del_mes(*args, **kw)
    assert memoria.fallos_de_memoria == {"incidencias_del_mes": 4}
    assert len(cli.leidas_inc) == 5


def test_f030_r33_lote_filtra_por_recurso_lo_precargado():
    from application.services.lecturas_lote import LecturasDelLote

    filas = [LineaIncidenciaSigrid(1, 200, 20260705, "CIV", None, "P"),
             LineaIncidenciaSigrid(2, 400, 20260705, "CIV", None, "P")]
    cli = ClienteInc(existentes=filas)
    memoria = LecturasDelLote(cli, 2)
    memoria.precargar([(OBRA, [], [_inc(), _inc(id=8, recurso_ide=400)])],
                      _ajustes(obra_pruebas_forzar=False))
    assert memoria.incidencias_del_mes([400], 2026, 7) == [filas[1]]
    assert memoria.fallos_de_memoria == {}


# ============================ contrato (T15) ============================= #
@pytest.fixture
def api(monkeypatch):
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from interface_adapters.api import app as modulo_app

    from tests.test_f050_endpoint_propuesta import AJUSTES

    def fabricar(cli, **ajustes):
        monkeypatch.setattr(modulo_app, "SigridWriteClient",
                            lambda **kw: cli)
        st = SimpleNamespace(**{**AJUSTES, "sigrid_lecturas_paralelas": 4,
                                **ajustes})
        return TestClient(modulo_app.build_app(st))
    return fabricar


def _json_linea(i, **kw):
    return {"registro_id": i, "ano": 2026, "mes": 7, "porcentaje": 0.4,
            "recurso_ide": 200, "nombre": "Acuna Mera, Antonio",
            "categoria": "Encargado", "empresa": 1, **kw}


def _json_inc(i=7, **kw):
    return {"id": i, "recurso_ide": 200, "empresa": 1, "codigo": "CIV",
            "ano": 2026, "mes": 7, "desde": 5, "hasta": 9, "paride": 0, **kw}


CLAVES_INC = {"id", "rol", "accion", "fecha_int", "hora_codigo", "paride",
              "parte_cod", "hmores_ide", "motivo"}


def test_f030_r31_contrato_preflight_con_incidencias(api):
    cuerpo = api(ClienteInc()).post("/api/registro/preflight", json={
        "obra": {"codigo": OBRA_ORIGEN}, "lineas": [_json_linea(1)],
        "incidencias": [_json_inc()]}).json()
    assert cuerpo["ok"] is True
    assert [set(x) for x in cuerpo["incidencias"]] == [CLAVES_INC] * 2
    assert [(x["id"], x["rol"], x["accion"], x["fecha_int"], x["hora_codigo"],
             x["parte_cod"], x["hmores_ide"], x["motivo"])
            for x in cuerpo["incidencias"]] == [
        (7, "ini", "escribir", 20260705, "CIV", "PT26/00251", None, None),
        (7, "fin", "escribir", 20260709, "CIZ", "PT26/00251", None, None)]
    assert cuerpo["resumen"]["escribir"] == 1     # las de % no cambian


def test_f030_r31_contrato_sin_incidencias_responde_como_hoy(api):
    peticion = {"obra": {"codigo": OBRA_ORIGEN}, "lineas": [_json_linea(1)]}
    hoy = api(ClienteInc()).post("/api/registro/preflight",
                                 json=peticion).json()
    vacia = api(ClienteInc()).post("/api/registro/preflight", json={
        **peticion, "incidencias": []}).json()
    assert "incidencias" not in hoy and vacia == hoy
    ej = api(ClienteEscribe()).post("/api/registro/ejecutar",
                                    json=peticion).json()
    assert "incidencias" not in ej and ej["ok"] is True


def test_f030_r31_contrato_ejecutar_devuelve_las_escritas(api):
    cli = ClienteEscribe()
    cuerpo = api(cli).post("/api/registro/ejecutar", json={
        "obra": {"codigo": OBRA_ORIGEN}, "lineas": [],
        "incidencias": [_json_inc(paride=None)]}).json()
    assert cuerpo["ok"] is True and cuerpo["escritas"] == []
    assert [(x["rol"], x["accion"], x["hmores_ide"], x["paride"])
            for x in cuerpo["incidencias"]] == [
        ("ini", "escribir", 70001, 0), ("fin", "escribir", 70002, 0)]
    assert [i["synckey"] for i in cli.inserts()] == [
        "porcentajes:inc:7:ini", "porcentajes:inc:7:fin"]


def test_f030_r31_contrato_lote_por_obra(api):
    cli = ClienteInc()
    cuerpo = api(cli).post("/api/registro/preflight-lote", json={
        "peticiones": [
            {"obra": {"codigo": OBRA_ORIGEN}, "lineas": [_json_linea(1)],
             "incidencias": [_json_inc()]},
            {"obra": {"codigo": OBRA_ORIGEN}, "lineas": [_json_linea(2)]}]}
    ).json()
    a, b = cuerpo["obras"]
    assert [x["accion"] for x in a["incidencias"]] == ["escribir"] * 2
    assert "incidencias" not in b
    assert len(cli.leidas_inc) == 1


def test_f030_r23_contrato_valores_que_omiten_sin_422(api):
    cuerpo = api(ClienteInc()).post("/api/registro/preflight", json={
        "obra": {"codigo": OBRA_ORIGEN}, "lineas": [_json_linea(1)],
        "incidencias": [{"id": 7, "codigo": "CIV", "ano": 2026, "mes": 7}]}
    ).json()
    assert [(x["accion"], x["motivo"]) for x in cuerpo["incidencias"]] == [
        ("omitir", MOTIVO_SIN_EMPRESA)] * 2


def test_f030_r23_contrato_empresas_mezcladas_422(api):
    r = api(ClienteInc()).post("/api/registro/preflight", json={
        "obra": {"codigo": OBRA_ORIGEN}, "lineas": [_json_linea(1)],
        "incidencias": [_json_inc(empresa=2)]})
    assert r.status_code == 422


# ============================= script (T18) ============================== #
def _script(monkeypatch, cli, *argv, **ajustes):
    import prueba_escritura_porcentajes as script

    monkeypatch.setattr(script, "get_settings", lambda: _ajustes(**ajustes))
    monkeypatch.setattr(script, "_cliente", lambda st: cli)
    monkeypatch.setattr("sys.argv", ["prueba_escritura_porcentajes.py", *argv])
    script.main()
    return script


def test_f030_r35_script_preflight_solo_la_incidencia(monkeypatch, capsys):
    cli = ClienteEscribe()
    script = _script(monkeypatch, cli, "preflight", "--ano", "2026", "--mes",
                     "7", "--incidencia", "200:civ:5:9")
    salida = capsys.readouterr().out
    assert "[escribir     ] inc=990101 ini CIV fec=20260705 parte=PT26/00251" \
        in salida
    assert "[escribir     ] inc=990101 fin CIZ fec=20260709 parte=PT26/00251" \
        in salida
    assert "reg=9000" not in salida                 # sin las líneas de ejemplo
    assert cli.escritos == []
    assert script.ID_INCIDENCIA_PRUEBA == 990101


def test_f030_r35_script_ejecutar_dry_run_y_confirmado(monkeypatch, capsys):
    cli = ClienteEscribe()
    _script(monkeypatch, cli, "ejecutar", "--ano", "2026", "--mes", "7",
            "--incidencia", "200:CIV:5:9")
    assert "DRY-RUN" in capsys.readouterr().out and cli.escritos == []
    _script(monkeypatch, cli, "ejecutar", "--confirmar", "--ano", "2026",
            "--mes", "7", "--incidencia", "200:CIV:5:9",
            "--incidencia", "400:CIV:12:12")
    salida = capsys.readouterr().out
    assert [i["synckey"] for i in cli.inserts()] == [
        "porcentajes:inc:990101:ini", "porcentajes:inc:990101:fin",
        "porcentajes:inc:990102:ini", "porcentajes:inc:990102:fin"]
    assert {i["tex"] for i in cli.inserts()} == {"PRUEBA-PORC"}
    assert {i["can"] for i in cli.inserts()} == {0.0}
    assert "INCIDENCIA inc=990101 ini escribir hmores.ide=70001" in salida
    assert "escritas=0" in salida


def test_f030_r35_script_verificar_por_synckey(monkeypatch, capsys):
    cli = ClienteEscribe()
    _script(monkeypatch, cli, "ejecutar", "--confirmar", "--ano", "2026",
            "--mes", "7", "--incidencia", "200:CIV:5:9")
    capsys.readouterr()
    _script(monkeypatch, cli, "verificar", "--incidencia", "200:CIV:5:9")
    salida = capsys.readouterr().out
    assert "porcentajes:inc:990101:ini: hmores.ide=70001 reside=200 " \
           "fec=20260705" in salida
    assert "porcentajes:inc:990101:fin: hmores.ide=70002 reside=200 " \
           "fec=20260709" in salida


@pytest.mark.parametrize("valor", ["200:CIV:5", "x:CIV:5:9", "200::5:9",
                                   "200:CIV:a:9", "200:CIV:5:9:1"])
def test_f030_r35_script_incidencia_mal_escrita(monkeypatch, valor):
    with pytest.raises(SystemExit):
        _script(monkeypatch, ClienteEscribe(), "preflight", "--incidencia",
                valor)


# ======================= mutación (T21): huecos ========================== #
def test_f030_r24_defectos_de_entrada_y_accion():
    """Lo que no se manda vale 0 (sin partida, sin periodo), no 1."""
    from domain.models.registro_models import AccionIncidencia
    from interface_adapters.api.app import IncidenciaIn

    entrada = IncidenciaEntrada(id=1, recurso_ide=200, empresa=1,
                                codigo="CIV", ano=2026, mes=7, desde=5,
                                hasta=9)
    assert entrada.paride == 0
    assert IncidenciaIn(id=1, codigo="CIV", ano=2026, mes=7).paride == 0
    a = AccionIncidencia(id=1, rol="ini", accion="omitir", fecha_int=0)
    assert (a.recurso_ide, a.ano, a.mes, a.hora_ide, a.hora_codigo, a.pre,
            a.paride, a.motivo, a.parte_cod, a.hmores_ide, a.destino,
            a.aviso, a.caa_ide) == (None, 0, 0, None, None, 0.0, 0, None,
                                     None, None, "obra", None, 0)


def test_f030_r24_ejecutar_sin_partida_inserta_paride_cero():
    cli = ClienteEscribe()
    _ej(cli, [], [_inc(paride=0)])
    assert [i["paride"] for i in cli.inserts()] == [0, 0]


def test_f030_r31_el_log_cuenta_las_que_se_escriben(caplog):
    import logging

    caplog.set_level(logging.INFO, "application.pipelines.registro_pipeline")
    # Una que se escribe (2 líneas) y dos que no (4): las cuentas no son
    # simétricas, así que «escribir» no puede salir de contar las otras.
    _pf(ClienteInc(), [], [_inc(), _inc(id=8, recurso_ide=300),
                           _inc(id=9, recurso_ide=300)])
    [linea_log] = [r.getMessage() for r in caplog.records
                   if "incidencias obra=" in r.getMessage()]
    assert linea_log.endswith("lineas=6 escribir=2")


class _ClientePrecarga(ClienteInc):
    """Anota las partidas cuya cuenta se precarga; el 500 tiene las dos
    horas de incidencia con subcuenta y una hora sin ella que no es de la
    incidencia."""

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.horas[500] = [
            HoraRecurso(5, "MENC", None, 9000.0, caa_cod="00000.CIMO03"),
            HoraRecurso(9, "HEGR", None, 30.0),
            HoraRecurso(71, "CIV", "Vacaciones(V)", 12.5,
                        caa_cod="00000.CIMO07"),
            HoraRecurso(79, "CIZ", "Fin de Incidencia", 0.0,
                        caa_cod="00000.CIMO07")]
        self.precargadas: list[list[int]] = []

    def partidas_de_lineas(self, parides):
        self.precargadas.append(sorted(parides))
        return super().partidas_de_lineas(parides)


def test_f030_r33_lote_precarga_la_cuenta_solo_si_falta_subcuenta():
    """La del 200 (su `CIZ` sin subcuenta) se precarga; la del 500 (las dos
    con subcuenta) y la de una incidencia sin recurso, no."""
    from application.services.lecturas_lote import LecturasDelLote

    cli = _ClientePrecarga()
    LecturasDelLote(cli, 2).precargar([(OBRA, [], [
        _inc(paride=80001), _inc(id=8, recurso_ide=500, paride=80002),
        _inc(id=9, recurso_ide=None, paride=80003)])], _ajustes())
    assert cli.precargadas == [[80001]]


class _ClienteVerifica(ClienteEscribe):
    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.pedidas: list[set[str]] = []

    def lineas_por_synckey(self, claves):
        self.pedidas.append(set(claves))
        return super().lineas_por_synckey(claves)


@pytest.mark.parametrize("argv, incidencias", [
    ((), [990101]),
    (("--incidencia", "200:CIV:5:9", "--incidencia", "400:CIV:1:2"),
     [990101, 990102])])
def test_f030_r35_script_verificar_pide_justo_esas_synckeys(monkeypatch,
                                                            argv, incidencias):
    cli = _ClienteVerifica()
    _script(monkeypatch, cli, "verificar", *argv)
    assert cli.pedidas == [
        {"porcentajes:900001", "porcentajes:900002", "porcentajes:900003",
         *(f"porcentajes:inc:{i}:{rol}" for i in incidencias
           for rol in ("ini", "fin"))}]
