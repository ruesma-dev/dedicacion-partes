# tests/test_f069_reglas_importe.py
"""F-069 · T2: el precio y la línea de un vinculado de CANTIDAD (R17-R22).

- Por % (`VP` en km, `VIAJE` en €): `can` = el del titular (sin
  normalizar, D8), `pre` = el importe del mes (en km, `round(km ×
  precio_km, 2)`, D10) y `tot = round(can × pre, 2)`, ignorando
  `reshor.pre` (R17).
- Por obra (`CAJA`): `can` 1, `pre` = `tot` = la cantidad de esa línea,
  aunque el % sea otro (R18, D12).
- La hora es SIEMPRE la por defecto del recurso, tenga o no precio (R19).
- Nula, 0, copiada sin revisar, sin hora o sin `precio_km`: omitido con su
  motivo (≤ 300, con tipo y código; en caja, con la obra) (R20-R22, D4,
  D11, D13).

Sin red ni BBDD; los `ide` son inventados.
"""
from __future__ import annotations

import pytest
from application.services.reglas_vinculados import (
    MOTIVO_CAJA_CERO,
    MOTIVO_FALTA_CAJA,
    MOTIVO_FALTA_IMPORTE,
    MOTIVO_IMPORTE_CERO,
    MOTIVO_SIN_HORA,
    MOTIVO_SIN_IMPORTE,
    MOTIVO_SIN_PRECIO_KM,
    MOTIVO_SIN_REVISAR,
    decidir_vinculados,
    precio_del_vinculado,
)
from domain.models.registro_models import (
    AccionLinea,
    HoraRecurso,
    LineaEntrada,
    VinculadoEntrada,
)

#: Horas por defecto de los vinculados de cantidad, con `pre` 0 como los
#: 44 de 45 `VP` de Sigrid (y una con precio, que se ignora).
HORAS = {
    20: [HoraRecurso(41, "KM", None, 0.0, defecto=True)],
    21: [HoraRecurso(42, "VI", None, 0.0, defecto=True)],
    22: [HoraRecurso(43, "CO", None, 0.0, defecto=True)],
    23: [HoraRecurso(44, "KM", None, 600.0, defecto=True)],
    24: [HoraRecurso(45, "KM", None, 0.0)],          # sin hora por defecto
    10: [HoraRecurso(31, "OTEL", None, 30.0, defecto=True)],
}


def _titular(**kw) -> AccionLinea:
    datos = dict(registro_id=12, accion="escribir", ano=2026, mes=11,
                 fecha_int=20261130, nombre="Acuna Mera, Antonio",
                 recurso_ide=200, hora_ide=5, hora_codigo="MENC", can=0.6,
                 pre=9000.0, tot=5400.0, destino="obra", paride=80001,
                 partida_cod="CI.1.10")
    datos.update(kw)
    return AccionLinea(**datos)


def _km(recurso: int = 20, **kw) -> VinculadoEntrada:
    datos = dict(recurso_ide=recurso, tipo="VP", tipo_res="KILOMETROS",
                 cod=f"VP{recurso:04d}", importe_mensual=True, unidad="km",
                 reparto="pct", cantidad=100.0, copiado=False,
                 comentario=None, precio_km=0.2)
    datos.update(kw)
    return VinculadoEntrada(**datos)


def _viaje(**kw) -> VinculadoEntrada:
    datos = dict(recurso_ide=21, tipo="VIAJE", tipo_res="VIAJES",
                 cod="VI0021", importe_mensual=True, unidad="eur",
                 reparto="pct", cantidad=45.6)
    datos.update(kw)
    return VinculadoEntrada(**datos)


def _caja(**kw) -> VinculadoEntrada:
    datos = dict(recurso_ide=22, tipo="CAJA", tipo_res="CAJA OBRA",
                 cod="CA0022", importe_mensual=True, unidad="eur",
                 reparto="obra", cantidad=80.0)
    datos.update(kw)
    return VinculadoEntrada(**datos)


def _linea(*vs: VinculadoEntrada) -> LineaEntrada:
    return LineaEntrada(registro_id=12, ano=2026, mes=11, porcentaje=0.6,
                        recurso_ide=200, vinculados=list(vs))


def _uno(v: VinculadoEntrada, **titular):
    [av] = decidir_vinculados(_titular(**titular), _linea(v), HORAS,
                              obra="0678")
    return av


# ============================== R17 · por % ============================== #
def test_f069_r17_km_al_60_por_ciento_pre_20_y_tot_12():
    av = _uno(_km())
    assert (av.accion, av.hora_ide, av.hora_codigo) == ("escribir", 41, "KM")
    assert (av.can, av.pre, av.tot) == (0.6, 20.0, 12.0)
    assert (av.km, av.precio_km, av.reparto) == (100.0, 0.2, "pct")


def test_f069_r17_km_redondeo_del_importe_y_del_total():
    # 724,5 km × 0,20 = 144,90; al 33,33 % ⇒ 48,30 (round(0.3333 × 144.9)).
    av = _uno(_km(cantidad=724.5), can=0.3333)
    assert (av.pre, av.tot) == (144.9, round(0.3333 * 144.9, 2))
    av = _uno(_km(cantidad=0.07, precio_km=0.2))
    assert av.pre == 0.01                       # round(0.014, 2)


def test_f069_r17_viaje_45_60_al_60_por_ciento_tot_27_36():
    av = _uno(_viaje())
    assert (av.accion, av.hora_codigo, av.can, av.pre, av.tot) == (
        "escribir", "VI", 0.6, 45.6, 27.36)
    assert (av.km, av.precio_km, av.reparto) == (None, None, "pct")


def test_f069_r17_d8_sin_normalizar_y_el_reshor_pre_se_ignora():
    av = _uno(_km(recurso=23), can=0.45)
    assert (av.can, av.pre, av.tot) == (0.45, 20.0, 9.0)   # no 600


# ============================== R18 · caja =============================== #
def test_f069_r18_caja_80_en_una_obra_can_1_pre_tot_80_aunque_el_pct_sea_30():
    av = _uno(_caja(), can=0.3)
    assert (av.accion, av.hora_codigo, av.can, av.pre, av.tot) == (
        "escribir", "CO", 1.0, 80.0, 80.0)
    assert (av.km, av.precio_km, av.reparto) == (None, None, "obra")


def test_f069_r18_caja_con_centimos():
    av = _uno(_caja(cantidad=12.34))
    assert (av.can, av.pre, av.tot) == (1.0, 12.34, 12.34)


# ========================= R19 · la hora, la suya ======================== #
@pytest.mark.parametrize("v, hora", [
    (_km(), "KM"), (_viaje(), "VI"), (_caja(), "CO")])
def test_f069_r19_la_hora_es_siempre_la_por_defecto(v, hora):
    horas = {**HORAS, v.recurso_ide: [
        HoraRecurso(90, "OTRA", None, 50.0),
        *HORAS[v.recurso_ide]]}
    [av] = decidir_vinculados(_titular(), _linea(v), horas, obra="0678")
    assert av.hora_codigo == hora


# ========================= R20-R22 · se omiten =========================== #
def test_f069_r20_por_pct_nula_falta_el_importe():
    av = _uno(_km(cantidad=None))
    assert av.accion == "omitir"
    assert av.motivo == MOTIVO_FALTA_IMPORTE.format(tipo="VP", cod="VP0020")
    assert "falta el importe" in av.motivo and "VP0020" in av.motivo


def test_f069_r20_por_pct_cero_importe_0():
    av = _uno(_viaje(cantidad=0.0))
    assert av.accion == "omitir"
    assert av.motivo == MOTIVO_IMPORTE_CERO.format(tipo="VIAJE", cod="VI0021")
    assert "importe 0" in av.motivo


def test_f069_r20_d13_caja_nula_falta_la_caja_del_mes_con_la_obra():
    av = _uno(_caja(cantidad=None))
    assert av.accion == "omitir"
    assert av.motivo == MOTIVO_FALTA_CAJA.format(tipo="CAJA", cod="CA0022",
                                                 obra="0678")
    assert "falta la caja del mes" in av.motivo and "0678" in av.motivo


def test_f069_r20_caja_cero_nada_en_esa_obra():
    av = _uno(_caja(cantidad=0.0))
    assert av.accion == "omitir"
    assert av.motivo == MOTIVO_CAJA_CERO.format(tipo="CAJA", cod="CA0022",
                                                obra="0678")


def test_f069_r21_d11_copiado_sin_revisar_se_omite():
    for v in (_km(copiado=True), _caja(copiado=True)):
        av = _uno(v)
        assert av.accion == "omitir"
        assert "copiado del mes anterior sin revisar" in av.motivo
    assert _uno(_km(copiado=True)).motivo == MOTIVO_SIN_REVISAR.format(
        tipo="VP", cod="VP0020", donde="")
    assert "0678" in _uno(_caja(copiado=True)).motivo


def test_f069_r22_sin_hora_por_defecto():
    av = _uno(_km(recurso=24))
    assert av.accion == "omitir"
    assert av.motivo == MOTIVO_SIN_HORA.format(tipo="VP", cod="VP0024")
    av = _uno(_caja(recurso_ide=99))                 # sin horas leídas
    assert av.motivo == MOTIVO_SIN_HORA.format(tipo="CAJA", cod="CA0022")


@pytest.mark.parametrize("precio", [None, 0.0, -0.2])
def test_f069_d10_km_sin_precio_por_km(precio):
    av = _uno(_km(precio_km=precio))
    assert av.accion == "omitir"
    assert av.motivo == MOTIVO_SIN_PRECIO_KM.format(tipo="VP", cod="VP0020")


def test_f069_r20_el_orden_sin_hora_antes_que_copiado_y_que_nula():
    av = _uno(_km(recurso=24, copiado=True, cantidad=None))
    assert av.motivo == MOTIVO_SIN_HORA.format(tipo="VP", cod="VP0024")
    av = _uno(_km(copiado=True, cantidad=None))
    assert "sin revisar" in av.motivo


def test_f069_r20_los_motivos_caben_en_300():
    largo = dict(tipo="X" * 30, cod="Y" * 30, obra="Z" * 30, donde=" " * 40)
    for m in (MOTIVO_FALTA_IMPORTE, MOTIVO_IMPORTE_CERO, MOTIVO_FALTA_CAJA,
              MOTIVO_CAJA_CERO, MOTIVO_SIN_REVISAR, MOTIVO_SIN_HORA,
              MOTIVO_SIN_PRECIO_KM):
        assert len(m.format(**largo)) <= 300


def test_f069_r20_titular_omitido_manda_sobre_la_cantidad():
    av = _uno(_km(cantidad=None), accion="omitir", motivo="sin código")
    assert av.motivo == "sigue al trabajador: sin código"


def test_f069_r20_el_titular_y_los_demas_como_siempre():
    vs = decidir_vinculados(
        _titular(), _linea(_km(cantidad=None), VinculadoEntrada(
            recurso_ide=10, tipo="TF", cod="TF-10")), HORAS, obra="0678")
    assert [v.accion for v in vs] == ["omitir", "escribir"]
    assert (vs[1].pre, vs[1].tot, vs[1].reparto, vs[1].km) == (
        30.0, 18.0, None, None)


# ===================== R24 · sin importe_mensual, F-044 ================== #
def test_f069_r24_sin_importe_mensual_el_pre_cero_sigue_sin_importe():
    av = _uno(VinculadoEntrada(recurso_ide=20, tipo="VP", cod="VP0020"))
    assert av.accion == "omitir"
    assert av.motivo == MOTIVO_SIN_IMPORTE.format(tipo="VP", cod="VP0020",
                                                  hora="KM")


def test_f069_r24_decidir_sin_obra_como_antes():
    [av] = decidir_vinculados(_titular(), _linea(VinculadoEntrada(
        recurso_ide=10, tipo="TF", cod="TF-10")), HORAS)
    assert (av.accion, av.pre, av.tot) == ("escribir", 30.0, 18.0)


# ===================== precio_del_vinculado, directo ===================== #
def test_f069_precio_del_vinculado_devuelve_las_siete_piezas():
    p = precio_del_vinculado(_km(), HORAS[20], 0.6, obra="0678")
    assert (p.hora.cod, p.can, p.pre, p.tot, p.km, p.precio_km,
            p.motivo) == ("KM", 0.6, 20.0, 12.0, 100.0, 0.2, None)
    p = precio_del_vinculado(_km(cantidad=None), HORAS[20], 0.6)
    assert (p.hora, p.motivo) == (None, MOTIVO_FALTA_IMPORTE.format(
        tipo="VP", cod="VP0020"))
