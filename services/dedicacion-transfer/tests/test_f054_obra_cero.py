# tests/test_f054_obra_cero.py
"""F-054 · parte B: la obra sin nada en la plataforma es un 0 % (R31-R34,
R36, R38; design §6.1-§6.2).

T11 (`-k reglas`): `reglas_obra_cero.py`, puro. Una línea mensual de
Sigrid de un recurso del lote es **sobrante** si ninguna acción de ese
recurso (en cualquier estado, también omitida) la cubre: normal, si alguna
va a esa obra; en la obra de postventa, si alguna de postventa resolvió esa
partida; en la VAR, si alguna tiene ese `var_paride`. En pruebas solo
cuentan las de la 0404, cubiertas si se reconocen (ya registrada, choque,
al 0) o alguna acción tiene su partida. Los vinculados, igual con sus
`AccionVinculado`. Parte cerrado o `synckey` de otro sistema ⇒ no
confirmable, con motivo; la nuestra huérfana y la `porcentajes:vin:`, sí.

T12 (`-k lote`): la lectura en la ronda A de `precargar` y
`RegistroLote.preflight_completo`.

Sin red ni BBDD.
"""
from __future__ import annotations

from application.services.reglas_obra_cero import (
    MOTIVO_CERRADO,
    MOTIVO_OTRO_SISTEMA,
    Cobertura,
    coberturas_de,
    confirmable,
    cubierta,
    reconocidas_de,
    sobrantes,
)
from domain.models.registro_models import (
    AccionLinea,
    AccionVinculado,
    Conflicto,
    LineaEntrada,
    LineaMensualSigrid,
    LineaSigrid,
    ObraEntrada,
    Preflight,
    Sobrante,
    VinculadoEntrada,
)

PV, VAR, PRU = "POSTV2", "VAR", "0404"
AJ = {"cod_pv": PV, "cod_var": VAR, "cod_pruebas": PRU}


def _m(ide, recurso=10, obra=694, cod=None, *, paride=0, hora="MADM",
       est=1, en_registro=True, synckey=None, can=0.2):
    return LineaMensualSigrid(
        hmores_ide=ide, recurso_ide=recurso, obra_ide=obra,
        obra_cod=cod or f"{obra:04d}", parte_ide=500 + obra,
        parte_cod=f"PT26/{obra}", parte_est=est, en_registro=en_registro,
        hora=hora, can=can, fec=20260930, paride=paride,
        partida_cod=f"P{paride}" if paride else None, synckey=synckey)


def _cub(lineas, cob, *, pruebas=False, reconocidas=()):
    return cubierta(lineas, cob, modo_pruebas=pruebas,
                    reconocidas=set(reconocidas), **AJ)


# --------------------------------- reglas -------------------------------- #
def test_f054_r31_reglas_normal_cubierta_si_alguna_va_a_esa_obra():
    assert _cub(_m(1), [Cobertura(694, "obra", 0, None)])
    assert not _cub(_m(1), [Cobertura(713, "obra", 0, None)])
    # Una de postventa o VAR a esa obra no cubre la normal.
    assert not _cub(_m(1), [Cobertura(694, "postventa", 0, None)])
    assert not _cub(_m(1), [Cobertura(694, "obra", 7, 7)])
    assert not _cub(_m(1), [])


def test_f054_r31_reglas_postventa_por_la_partida_resuelta():
    linea = _m(2, obra=999001, cod=PV, paride=81)
    assert _cub(linea, [Cobertura(694, "postventa", 81, None)])
    assert not _cub(linea, [Cobertura(694, "postventa", 82, None)])
    assert not _cub(linea, [Cobertura(999001, "obra", 81, None)])


def test_f054_r31_reglas_var_por_su_var_paride():
    linea = _m(3, obra=777, cod=VAR, paride=2105)
    assert _cub(linea, [Cobertura(777, "obra", 0, 2105)])
    assert not _cub(linea, [Cobertura(777, "obra", 2105, None)])
    assert not _cub(linea, [Cobertura(777, "obra", 0, 2106)])


def test_f054_r32_reglas_en_pruebas_reconocida_o_con_su_partida():
    linea = _m(4, obra=404, cod=PRU, paride=33)
    assert _cub(linea, [], pruebas=True, reconocidas={4})
    assert _cub(linea, [Cobertura(404, "obra", 33, None)], pruebas=True)
    assert not _cub(linea, [Cobertura(404, "obra", 34, None)], pruebas=True)
    # En pruebas no basta con ir a la obra.
    assert not _cub(linea, [Cobertura(404, "obra", 0, None)], pruebas=True)


def test_f054_r34_reglas_confirmable():
    assert confirmable(_m(1)) == (True, None)
    assert confirmable(_m(1, synckey="porcentajes:77")) == (True, None)
    assert confirmable(_m(1, synckey="porcentajes:vin:77:5000")) == (True,
                                                                     None)
    assert confirmable(_m(1, en_registro=False, est=3)) == (
        False, MOTIVO_CERRADO.format(parte="PT26/694"))
    assert confirmable(_m(1, synckey="partes:9")) == (
        False, MOTIVO_OTRO_SISTEMA.format(synckey="partes:9"))
    assert MOTIVO_CERRADO.format(parte="X") == "el parte X no está En registro"
    assert MOTIVO_OTRO_SISTEMA.format(synckey="s") == (
        "la línea es de otro sistema (synckey s)")


def _sob(mensuales, cob, **kw):
    return sobrantes(mensuales, cob, vinculados=kw.pop("vinculados", {}),
                     reconocidas=set(kw.pop("reconocidas", ())),
                     excluidos=set(kw.pop("excluidos", ())),
                     modo_pruebas=kw.pop("pruebas", False), **AJ)


def test_f054_r31_r33_reglas_sobrantes_ordenados_con_su_clave():
    cob = {10: [Cobertura(694, "obra", 0, None)], 20: []}
    r = _sob([_m(9, obra=713, paride=5, synckey="partes:1"), _m(1),
              _m(3, recurso=20, obra=694, en_registro=False, est=3),
              _m(2, recurso=99, obra=713)], cob)
    assert [s.hmores_ide for s in r] == [3, 9]
    assert r[1] == Sobrante(
        clave="cero:9", hmores_ide=9, recurso_ide=10, vinculado=None,
        obra_ide=713, obra_cod="0713", parte_cod="PT26/713", parte_est=1,
        hora="MADM", paride=5, partida_cod="P5", can=0.2,
        synckey="partes:1", confirmable=False,
        motivo="la línea es de otro sistema (synckey partes:1)")
    assert (r[0].confirmable, r[0].motivo) == (
        False, "el parte PT26/694 no está En registro")


def test_f054_d14_reglas_recurso_sin_lineas_en_el_lote_o_excluido_fuera():
    cob = {10: []}
    assert _sob([_m(1, recurso=20)], cob) == []
    assert _sob([_m(1)], cob, excluidos={10}) == []
    assert [s.hmores_ide for s in _sob([_m(1)], cob)] == [1]


def test_f054_r31_reglas_mesve_del_vinculado_no_es_del_trabajador():
    """La `MESVE` de su vinculado en el mismo parte es de OTRO recurso: no
    es sobrante del trabajador (ni del vinculado si no va en el lote)."""
    cob = {10: [Cobertura(694, "obra", 0, None)]}
    assert _sob([_m(5, recurso=5000, obra=713, hora="MESVE")], cob) == []


def test_f054_r32_reglas_en_pruebas_solo_las_de_la_0404():
    cob = {10: [Cobertura(404, "obra", 0, None)]}
    r = _sob([_m(1, obra=713), _m(2, obra=404, cod=PRU, paride=33),
              _m(3, obra=404, cod=PRU, paride=34)], cob, pruebas=True,
             reconocidas={3})
    assert [s.hmores_ide for s in r] == [2]


def test_f054_r38_reglas_vinculado_con_sus_acciones_y_su_dato():
    cob = {10: [Cobertura(694, "obra", 0, None)],
           5000: [Cobertura(694, "obra", 81, None)]}
    vin = {5000: {"tipo": "TF", "cod": "TEL1", "titular_ide": 10}}
    r = _sob([_m(1, recurso=5000, obra=694, hora="MESVE"),
              _m(2, recurso=5000, obra=713, hora="OTEL",
                 synckey="porcentajes:vin:4:5000")], cob, vinculados=vin)
    assert [(s.hmores_ide, s.vinculado, s.hora, s.confirmable)
            for s in r] == [(2, vin[5000], "OTEL", True)]


def _pf(acciones=(), vinculados=(), conflictos=(), obra=694):
    return Preflight(obra_destino=ObraEntrada(ide=obra, codigo=f"{obra:04d}"),
                     obra_origen=ObraEntrada(ide=obra), forzada_pruebas=False,
                     acciones=list(acciones), vinculados=list(vinculados),
                     conflictos=list(conflictos))


def _a(rid, recurso, accion="escribir", **kw):
    return AccionLinea(registro_id=rid, accion=accion, ano=2026, mes=9,
                       fecha_int=20260930, recurso_ide=recurso, **kw)


def test_f054_r31_reglas_coberturas_de_toda_accion_tambien_omitida():
    lineas = [LineaEntrada(registro_id=1, ano=2026, mes=9, porcentaje=0.5,
                           recurso_ide=10),
              LineaEntrada(registro_id=2, ano=2026, mes=9, porcentaje=0.5,
                           recurso_ide=10, var_paride=2105, vinculados=[
                               VinculadoEntrada(recurso_ide=5000)])]
    pf = _pf([_a(1, 10, "omitir", motivo="x"),
              _a(2, 10, paride=2105, destino="obra")],
             [AccionVinculado(registro_id=2, recurso_ide=5000,
                              accion="omitir", ano=2026, mes=9,
                              fecha_int=20260930, paride=0)])
    assert coberturas_de(pf, lineas) == {
        10: [Cobertura(694, "obra", 0, None), Cobertura(694, "obra", 2105,
                                                        2105)],
        5000: [Cobertura(694, "obra", 0, 2105)]}


def test_f054_r32_reglas_reconocidas_ya_registrada_cero_y_choque():
    pf = _pf([_a(1, 10, "ya_registrado", hmores_ide=11),
              _a(2, 10, linea_cero={"ide": 12})],
             [AccionVinculado(registro_id=1, recurso_ide=5000,
                              accion="ya_registrado", ano=2026, mes=9,
                              fecha_int=20260930, hmores_ide=13)],
             [Conflicto(clave="k", recurso_ide=10, nombre=None, ano=2026,
                        mes=9, parte_cod=None, edita_ide=14,
                        a_cero_ides=[15], lineas=[LineaSigrid(
                            ide=16, reside=10, fecha_int=1, horide=None,
                            hora_codigo=None, can=0, tot=0, synckey=None)])])
    assert reconocidas_de(pf) == {11, 12, 13, 14, 15, 16}
